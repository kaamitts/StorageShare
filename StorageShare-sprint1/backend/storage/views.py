"""US-02: list storage points, filtered by district. US-07: partners add points."""

from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsPartner
from storage.hours import storage_point_is_open
from storage.models import District, StoragePoint
from storage.serializers import (
    DistrictSerializer,
    PartnerStoragePointSerializer,
    StoragePointCardSerializer,
    StoragePointCreateSerializer,
    StoragePointDetailSerializer,
)


def _boolean_query_param(request, name):
    value = request.query_params.get(name)
    if value is None:
        return None
    try:
        return serializers.BooleanField().run_validation(value)
    except serializers.ValidationError as error:
        raise ValidationError({name: error.detail}) from error


class StoragePointListView(generics.ListCreateAPIView):
    """GET /api/storage-points/?district=medeu — any logged-in user.
    POST /api/storage-points/ — partners only (US-07).

    Without the parameter the whole active list is returned; with it, only the
    points of that district. An unknown district is rejected with 400 rather
    than answered with an empty list, so a typo in the frontend is visible
    instead of looking like "no points here".
    """

    serializer_class = StoragePointCardSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), IsPartner()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.request.method == "POST":
            return StoragePointCreateSerializer
        return StoragePointCardSerializer

    def perform_create(self, serializer):
        serializer.save(partner=self.request.user)

    def get_queryset(self):
        queryset = StoragePoint.objects.active().select_related("partner")

        district = self.request.query_params.get("district")
        if district is not None:
            district = district.strip().lower()
            if district not in District.values:
                raise ValidationError(
                    {"district": [
                        f'"{district}" is not a valid district. '
                        f"Valid values: {', '.join(District.values)}."
                    ]}
                )
            queryset = queryset.in_district(district)

        is_24_hours = _boolean_query_param(self.request, "is_24_hours")
        if is_24_hours is not None:
            queryset = queryset.filter(is_24_hours=is_24_hours)

        open_now = _boolean_query_param(self.request, "open_now")
        if open_now:
            now = timezone.now()
            return [point for point in queryset if storage_point_is_open(point, now)]
        return queryset


class PartnerStoragePointListView(generics.ListAPIView):
    """List all active and inactive points belonging to the logged-in partner."""

    serializer_class = PartnerStoragePointSerializer
    permission_classes = [permissions.IsAuthenticated, IsPartner]
    pagination_class = None

    def get_queryset(self):
        return StoragePoint.objects.filter(partner=self.request.user)


class StoragePointDetailView(generics.RetrieveAPIView):
    """GET /api/storage-points/<id>/ — the storage point page.

    Only active points are reachable: a point the partner has hidden returns
    404, the same answer as an id that never existed. A hidden point is not
    in the list either, so the two endpoints agree.
    """

    serializer_class = StoragePointDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = StoragePoint.objects.active()


class DistrictListView(APIView):
    """GET /api/districts/ — the fixed list for the filter control."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(DistrictSerializer(DistrictSerializer.all_districts(), many=True).data)
