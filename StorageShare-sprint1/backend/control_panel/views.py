from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsSuperUser
from bookings.models import Booking, BookingStatus
from bookings.services import BookingConflict, admin_cancel_booking
from control_panel.serializers import (
    ActiveStateSerializer,
    AdminBookingSerializer,
    AdminStoragePointSerializer,
    AdminUserSerializer,
)
from storage.models import District, StoragePoint

User = get_user_model()


class AdminAPIViewMixin:
    permission_classes = [permissions.IsAuthenticated, IsSuperUser]


class AdminDashboardView(AdminAPIViewMixin, APIView):
    def get(self, request):
        counts = {
            "bookings": Booking.objects.count(),
            "active_bookings": Booking.objects.filter(
                status__in=(BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN)
            ).count(),
            "storage_points": StoragePoint.objects.count(),
            "active_storage_points": StoragePoint.objects.filter(is_active=True).count(),
            "travelers": User.objects.filter(role=User.Role.TRAVELER, is_superuser=False).count(),
            "partners": User.objects.filter(role=User.Role.PARTNER, is_superuser=False).count(),
        }
        return Response(counts)


class AdminBookingListView(AdminAPIViewMixin, generics.ListAPIView):
    serializer_class = AdminBookingSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Booking.objects.select_related("traveler", "storage_point")
        search = self.request.query_params.get("search", "").strip()[:120]
        status_filter = self.request.query_params.get("status")
        if status_filter:
            if status_filter not in BookingStatus.values:
                raise ValidationError({"status": "Unknown booking status."})
            queryset = queryset.filter(status=status_filter)
        if search:
            search_filter = (
                Q(traveler__email__icontains=search)
                | Q(traveler__full_name__icontains=search)
                | Q(storage_point__name__icontains=search)
                | Q(storage_point__address__icontains=search)
            )
            if search.isdecimal():
                search_filter |= Q(pk=int(search))
            queryset = queryset.filter(search_filter)
        return queryset.order_by("-created_at", "-id")


class AdminBookingCancelView(AdminAPIViewMixin, APIView):
    def post(self, request, pk):
        try:
            booking, changed = admin_cancel_booking(booking_id=pk)
        except BookingConflict as error:
            return Response({"detail": str(error.detail)}, status=status.HTTP_409_CONFLICT)
        return Response(
            {**AdminBookingSerializer(booking).data, "changed": changed},
            status=status.HTTP_200_OK,
        )


class AdminBookingDeleteView(AdminAPIViewMixin, APIView):
    @transaction.atomic
    def delete(self, request, pk):
        booking = get_object_or_404(Booking.objects.select_for_update(), pk=pk)
        booking.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminStoragePointListView(AdminAPIViewMixin, generics.ListAPIView):
    serializer_class = AdminStoragePointSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = StoragePoint.objects.select_related("partner").annotate(
            bookings_count=Count("bookings")
        )
        search = self.request.query_params.get("search", "").strip()[:120]
        district = self.request.query_params.get("district")
        active = self.request.query_params.get("active")
        if district:
            if district not in District.values:
                raise ValidationError({"district": "Unknown district."})
            queryset = queryset.filter(district=district)
        if active is not None:
            try:
                active = serializers.BooleanField().run_validation(active)
            except serializers.ValidationError as error:
                raise ValidationError({"active": error.detail}) from error
            queryset = queryset.filter(is_active=active)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(address__icontains=search)
                | Q(partner__email__icontains=search)
                | Q(partner__full_name__icontains=search)
            )
        return queryset.order_by("name", "id")


class AdminStoragePointActiveView(AdminAPIViewMixin, APIView):
    @transaction.atomic
    def post(self, request, pk):
        point = get_object_or_404(StoragePoint.objects.select_for_update(), pk=pk)
        serializer = ActiveStateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        point.is_active = serializer.validated_data["is_active"]
        point.save(update_fields=["is_active", "updated_at"])
        return Response(AdminStoragePointSerializer(point).data)


class AdminStoragePointDeleteView(AdminAPIViewMixin, APIView):
    @transaction.atomic
    def delete(self, request, pk):
        point = get_object_or_404(StoragePoint.objects.select_for_update(), pk=pk)
        if point.bookings.exists():
            return Response(
                {"detail": "This point has booking history. Deactivate it to preserve records."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            point.delete()
        except ProtectedError:
            return Response(
                {"detail": "This point has related records and cannot be deleted."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserListView(AdminAPIViewMixin, generics.ListAPIView):
    serializer_class = AdminUserSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = User.objects.filter(is_superuser=False).annotate(
            bookings_count=Count("bookings", distinct=True),
            storage_points_count=Count("storage_points", distinct=True),
        )
        role = self.request.query_params.get("role")
        active = self.request.query_params.get("active")
        search = self.request.query_params.get("search", "").strip()[:120]
        if role:
            if role not in User.Role.values:
                raise ValidationError({"role": "Unknown user role."})
            queryset = queryset.filter(role=role)
        if active is not None:
            try:
                active = serializers.BooleanField().run_validation(active)
            except serializers.ValidationError as error:
                raise ValidationError({"active": error.detail}) from error
            queryset = queryset.filter(is_active=active)
        if search:
            queryset = queryset.filter(
                Q(email__icontains=search)
                | Q(full_name__icontains=search)
                | Q(phone__icontains=search)
            )
        return queryset.order_by("-created_at", "-id")


class AdminUserActiveView(AdminAPIViewMixin, APIView):
    @transaction.atomic
    def post(self, request, pk):
        user = get_object_or_404(User.objects.select_for_update(), pk=pk, is_superuser=False)
        serializer = ActiveStateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.is_active = serializer.validated_data["is_active"]
        user.save(update_fields=["is_active"])
        return Response(AdminUserSerializer(user).data)


class AdminUserDeleteView(AdminAPIViewMixin, APIView):
    @transaction.atomic
    def delete(self, request, pk):
        user = get_object_or_404(User.objects.select_for_update(), pk=pk, is_superuser=False)
        if user.bookings.exists() or user.storage_points.exists():
            return Response(
                {"detail": "This user has booking or storage history. Deactivate the account instead."},
                status=status.HTTP_409_CONFLICT,
            )
        try:
            user.delete()
        except ProtectedError:
            return Response(
                {"detail": "This user has related records and cannot be deleted."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
