from django.urls import path

from bookings import views

app_name = "bookings"

urlpatterns = [
    path("", views.BookingCreateView.as_view(), name="booking-create"),
    path("history/", views.BookingHistoryView.as_view(), name="booking-history"),
    path("pending/", views.PendingBookingView.as_view(), name="booking-pending"),
    path("<int:pk>/pay/", views.BookingPayView.as_view(), name="booking-pay"),
    path("<int:pk>/cancel/", views.BookingCancelView.as_view(), name="booking-cancel"),
    path(
        "by-token/<str:token>/",
        views.BookingByTokenView.as_view(),
        name="booking-by-token",
    ),
    path(
        "by-token/<str:token>/check-in/",
        views.BookingCheckInView.as_view(),
        name="booking-check-in",
    ),
    path(
        "by-token/<str:token>/check-out/",
        views.BookingCheckOutView.as_view(),
        name="booking-check-out",
    ),
]
