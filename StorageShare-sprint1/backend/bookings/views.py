from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsPartner, IsTraveler
from bookings.models import Booking, BookingStatus
from bookings.serializers import (
    BookingHistorySerializer,
    BookingSerializer,
    PartnerBookingSerializer,
    PartnerCheckInSerializer,
)
from bookings.services import (
    BookingPaymentExpired,
    check_in_booking,
    check_out_booking,
    confirm_booking_payment,
    get_booking_for_partner,
)


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsTraveler]

    def perform_create(self, serializer):
        serializer.save(traveler=self.request.user)


class BookingHistoryView(generics.ListAPIView):
    """The traveler's own bookings, without the ones still awaiting payment."""

    serializer_class = BookingHistorySerializer
    permission_classes = [permissions.IsAuthenticated, IsTraveler]

    def get_queryset(self):
        return (
            Booking.objects.filter(traveler=self.request.user)
            .exclude(status=BookingStatus.AWAITING_PAYMENT)
            .select_related("storage_point")
            .order_by("-drop_off_at", "-id")
        )


class BookingPayView(APIView):
    """Mock Pay button: confirms the booking. No payment provider is called."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            booking, _changed = confirm_booking_payment(user=request.user, booking_id=pk)
        except BookingPaymentExpired as error:
            return Response(
                {"detail": str(error.detail), "code": "booking_payment_expired"},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)


class PartnerBookingListView(generics.ListAPIView):
    """US-08: paid bookings of the logged-in partner's own storage points."""

    serializer_class = PartnerBookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartner]
    pagination_class = None

    def get_queryset(self):
        return (
            Booking.objects.filter(storage_point__partner=self.request.user)
            .exclude(status__in=(BookingStatus.AWAITING_PAYMENT, BookingStatus.EXPIRED))
            .select_related("storage_point")
            .order_by("drop_off_at", "id")
        )


class BookingByTokenView(APIView):
    """US-09: GET /api/bookings/by-token/<token>/ — the partner's check-in page."""

    permission_classes = [permissions.IsAuthenticated, IsPartner]

    def get(self, request, token):
        booking = get_booking_for_partner(partner=request.user, token=token)
        return Response(PartnerCheckInSerializer(booking).data)


class BookingCheckInView(APIView):
    """US-09: POST /api/bookings/by-token/<token>/check-in/"""

    permission_classes = [permissions.IsAuthenticated, IsPartner]

    def post(self, request, token):
        booking = check_in_booking(partner=request.user, token=token)
        return Response(PartnerCheckInSerializer(booking).data)


class BookingCheckOutView(APIView):
    """US-09: POST /api/bookings/by-token/<token>/check-out/"""

    permission_classes = [permissions.IsAuthenticated, IsPartner]

    def post(self, request, token):
        booking = check_out_booking(partner=request.user, token=token)
        return Response(PartnerCheckInSerializer(booking).data)
