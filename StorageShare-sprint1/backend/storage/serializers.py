"""Serializers for the storage point list (US-02 result cards)."""

from datetime import time
from decimal import Decimal

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
        fields = (
            "id", "name", "district", "district_code", "price_per_bag_per_hour",
            "latitude", "longitude",
        )
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
            "latitude",
            "longitude",
            "opens_at",
            "closes_at",
            "is_24_hours",
            "security_notes",
            "price_per_bag_per_hour",
        )
        read_only_fields = fields


class PartnerStoragePointSerializer(serializers.ModelSerializer):
    """Fields shown to a partner for their own active and inactive points."""

    district = serializers.CharField(source="get_district_display", read_only=True)
    district_code = serializers.CharField(source="district", read_only=True)
    opens_at = serializers.TimeField(format="%H:%M", read_only=True)
    closes_at = serializers.TimeField(format="%H:%M", read_only=True)

    class Meta:
        model = StoragePoint
        fields = (
            "id", "name", "address", "latitude", "longitude", "district", "district_code",
            "price_per_bag_per_hour", "capacity_bags", "opens_at", "closes_at",
            "is_24_hours", "is_active",
        )
        read_only_fields = fields


class DistrictSerializer(serializers.Serializer):
    """The fixed district list, so the frontend filter is not hard-coded."""

    code = serializers.CharField()
    name = serializers.CharField()

    @staticmethod
    def all_districts():
        return [{"code": value, "name": label} for value, label in District.choices]


class StoragePointCreateSerializer(serializers.ModelSerializer):
    """US-07: the partner's form for a new storage point.

    The partner is taken from the logged-in user in the view, never from the body.
    """

    name = serializers.CharField(max_length=120, trim_whitespace=True)
    address = serializers.CharField(max_length=255, trim_whitespace=True)
    district = serializers.ChoiceField(choices=District.choices)
    price_per_bag_per_hour = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=0,
    )
    capacity_bags = serializers.IntegerField(min_value=1, max_value=32767)
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, min_value=Decimal("-90"),
        max_value=Decimal("90"), required=False, allow_null=True,
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, min_value=Decimal("-180"),
        max_value=Decimal("180"), required=False, allow_null=True,
    )
    closes_at = serializers.TimeField(required=False, allow_null=True)
    opens_at = serializers.TimeField(required=False, allow_null=True)
    is_24_hours = serializers.BooleanField(default=False)
    security_notes = serializers.CharField(
        required=False, allow_blank=True, default="", trim_whitespace=True,
    )

    class Meta:
        model = StoragePoint
        fields = (
            "id",
            "partner",
            "name",
            "address",
            "latitude",
            "longitude",
            "district",
            "price_per_bag_per_hour",
            "capacity_bags",
            "opens_at",
            "closes_at",
            "is_24_hours",
            "security_notes",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "partner", "is_active", "created_at")

    def validate(self, attrs):
        if (attrs.get("latitude") is None) != (attrs.get("longitude") is None):
            raise serializers.ValidationError({
                "latitude": ["Latitude and longitude must be provided together."],
                "longitude": ["Latitude and longitude must be provided together."],
            })

        if attrs["is_24_hours"]:
            # Keep the existing non-null time columns and use their established
            # equal-times convention for compatibility with older records.
            attrs["opens_at"] = time.min
            attrs["closes_at"] = time.min
            return attrs

        if attrs.get("opens_at") is None:
            raise serializers.ValidationError({"opens_at": ["This field is required."]})
        if attrs.get("closes_at") is None:
            raise serializers.ValidationError({"closes_at": ["This field is required."]})
        if attrs["closes_at"] == attrs["opens_at"]:
            raise serializers.ValidationError(
                {"closes_at": ["Choose 24-hour mode for equal opening and closing times."]}
            )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Same "08:00" format as the detail page.
        data["opens_at"] = instance.opens_at.strftime("%H:%M")
        data["closes_at"] = instance.closes_at.strftime("%H:%M")
        return data
