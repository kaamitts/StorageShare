from django.urls import path

from storage import views

app_name = "storage"

urlpatterns = [
    path("storage-points/", views.StoragePointListView.as_view(), name="storage-point-list"),
    path(
        "storage-points/<int:pk>/",
        views.StoragePointDetailView.as_view(),
        name="storage-point-detail",
    ),
    path("districts/", views.DistrictListView.as_view(), name="district-list"),
]
