"""Serializers for the storage point list (US-02 result cards)."""

from rest_framework import serializers

from storage.models import District, StoragePoint


class StoragePointCardSerializer(serializers.ModelSerializer):
    """What one card in the result list shows.

    The card deliberately carries only what US-02 asks for — name, district and
    price. The full details belong to the detail page (US-03).
    """

    district = serializers.CharField(source="get_district_display", read_only=True)
    district_code = serializers.CharField(source="district", read_only=True)

    class Meta:
        model = StoragePoint
        fields = ("id", "name", "district", "district_code", "price_per_bag_per_hour")
        read_only_fields = fields


class StoragePointDetailSerializer(serializers.ModelSerializer):
    """The storage point page (US-03): everything a traveler needs before booking."""

    district = serializers.CharField(source="get_district_display", read_only=True)
    district_code = serializers.CharField(source="district", read_only=True)
    # "08:00" reads better on the page than the default "08:00:00".
    opens_at = serializers.TimeField(format="%H:%M", read_only=True)
    closes_at = serializers.TimeField(format="%H:%M", read_only=True)

    class Meta:
        model = StoragePoint
        fields = (
            "id",
            "name",
            "district",
            "district_code",
            "address",
            "opens_at",
            "closes_at",
            "security_notes",
            "price_per_bag_per_hour",
        )
        read_only_fields = fields


class DistrictSerializer(serializers.Serializer):
    """The fixed district list, so the frontend filter is not hard-coded."""

    code = serializers.CharField()
    name = serializers.CharField()

    @staticmethod
    def all_districts():
        return [{"code": value, "name": label} for value, label in District.choices]
