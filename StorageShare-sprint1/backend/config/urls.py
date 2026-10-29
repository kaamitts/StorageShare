from django.contrib import admin
from django.urls import include, path
from config.health import health

urlpatterns = [
    path("api/health/", health),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("storage.urls")),
]
