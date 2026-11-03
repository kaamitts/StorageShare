from rest_framework import serializers

from bookings.models import Booking
from bookings.services import create_booking, validate_booking_times
from storage.models import StoragePoint


class BookingSerializer(serializers.ModelSerializer):
    storage_point = serializers.PrimaryKeyRelatedField(
        queryset=StoragePoint.objects.active(),
        pk_field=serializers.IntegerField(min_value=1),
    )
    bags_count = serializers.IntegerField(min_value=1, max_value=32767)

    class Meta:
        model = Booking
        fields = (
            "id", "traveler", "storage_point", "drop_off_at", "pick_up_at",
            "bags_count", "total_price", "status", "created_at", "updated_at",
        )
        read_only_fields = (
            "id", "traveler", "total_price", "status", "created_at", "updated_at",
        )

    def validate(self, attrs):
        validate_booking_times(attrs["drop_off_at"], attrs["pick_up_at"])
        return attrs

    def create(self, validated_data):
        return create_booking(**validated_data)
