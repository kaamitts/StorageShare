from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings.serializers import BookingSerializer
from bookings.services import confirm_booking_payment


class IsTraveler(permissions.BasePermission):
    message = "Only travelers can create bookings."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_traveler


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsTraveler]

    def perform_create(self, serializer):
        serializer.save(traveler=self.request.user)


class BookingPayView(APIView):
    """Mock Pay button: confirms the booking. No payment provider is called."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        booking, _changed = confirm_booking_payment(user=request.user, booking_id=pk)
        return Response(BookingSerializer(booking).data, status=status.HTTP_200_OK)
