from django.urls import path

from control_panel import views

app_name = "control_panel"

urlpatterns = [
    path("dashboard/", views.AdminDashboardView.as_view(), name="dashboard"),
    path("bookings/", views.AdminBookingListView.as_view(), name="bookings"),
    path("bookings/<int:pk>/cancel/", views.AdminBookingCancelView.as_view(), name="booking-cancel"),
    path("bookings/<int:pk>/", views.AdminBookingDeleteView.as_view(), name="booking-delete"),
    path("storage-points/", views.AdminStoragePointListView.as_view(), name="storage-points"),
    path("storage-points/<int:pk>/active/", views.AdminStoragePointActiveView.as_view(), name="storage-point-active"),
    path("storage-points/<int:pk>/", views.AdminStoragePointDeleteView.as_view(), name="storage-point-delete"),
    path("users/", views.AdminUserListView.as_view(), name="users"),
    path("users/<int:pk>/active/", views.AdminUserActiveView.as_view(), name="user-active"),
    path("users/<int:pk>/", views.AdminUserDeleteView.as_view(), name="user-delete"),
]
