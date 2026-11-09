from django.urls import path

from bookings.views import BookingCreateView, BookingPayView

app_name = "bookings"

urlpatterns = [
    path("", BookingCreateView.as_view(), name="booking-create"),
    path("<int:pk>/pay/", BookingPayView.as_view(), name="booking-pay"),
]
