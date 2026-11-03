from rest_framework import generics, permissions

from bookings.serializers import BookingSerializer


class IsTraveler(permissions.BasePermission):
    message = "Only travelers can create bookings."

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_traveler


class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated, IsTraveler]

    def perform_create(self, serializer):
        serializer.save(traveler=self.request.user)
