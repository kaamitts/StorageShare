from django.urls import path

from bookings.views import BookingCreateView, BookingHistoryView, BookingPayView

app_name = "bookings"

urlpatterns = [
    path("", BookingCreateView.as_view(), name="booking-create"),
    path("history/", BookingHistoryView.as_view(), name="booking-history"),
    path("<int:pk>/pay/", BookingPayView.as_view(), name="booking-pay"),
]
