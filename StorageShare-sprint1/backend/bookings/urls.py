from django.urls import path

from bookings.views import BookingCreateView

app_name = "bookings"

urlpatterns = [
    path("", BookingCreateView.as_view(), name="booking-create"),
]