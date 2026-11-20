"""Role-based permissions shared by the apps."""

from rest_framework import permissions


class IsTraveler(permissions.BasePermission):
    message = "Only travelers can do this."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_traveler)


class IsPartner(permissions.BasePermission):
    message = "Only partners can do this."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_partner)


class IsSuperUser(permissions.BasePermission):
    """Only a Django superuser may use the private management API."""

    message = "Administrator access is required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )
