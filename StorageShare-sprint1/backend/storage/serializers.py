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
    opens_at = serializers.TimeField()
    closes_at = serializers.TimeField()
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
            "district",
            "price_per_bag_per_hour",
            "capacity_bags",
            "opens_at",
            "closes_at",
            "security_notes",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "partner", "is_active", "created_at")

    def validate(self, attrs):
        if attrs["closes_at"] <= attrs["opens_at"]:
            raise serializers.ValidationError(
                {"closes_at": ["Closing time must be later than opening time."]}
            )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Same "08:00" format as the detail page.
        data["opens_at"] = instance.opens_at.strftime("%H:%M")
        data["closes_at"] = instance.closes_at.strftime("%H:%M")
        return data
