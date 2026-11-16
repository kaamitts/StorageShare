from django.urls import path

from bookings import views

app_name = "partner"

urlpatterns = [
    path("bookings/", views.PartnerBookingListView.as_view(), name="partner-bookings"),
]
