from django.urls import path

from bookings import views
from storage.views import PartnerStoragePointDetailView, PartnerStoragePointListView

app_name = "partner"

urlpatterns = [
    path("bookings/", views.PartnerBookingListView.as_view(), name="partner-bookings"),
    path(
        "storage-points/",
        PartnerStoragePointListView.as_view(),
        name="partner-storage-points",
    ),
    path(
        "storage-points/<int:pk>/",
        PartnerStoragePointDetailView.as_view(),
        name="partner-storage-point-detail",
    ),
]
