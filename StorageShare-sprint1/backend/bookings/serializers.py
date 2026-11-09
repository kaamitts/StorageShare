from rest_framework import serializers

from bookings.models import Booking
from bookings.qr import has_active_qr, qr_svg_data_uri, qr_url
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


class BookingStoragePointSerializer(serializers.ModelSerializer):
    district = serializers.CharField(source="get_district_display", read_only=True)

    class Meta:
        model = StoragePoint
        fields = ("id", "name", "address", "district")
        read_only_fields = fields


class BookingHistorySerializer(serializers.ModelSerializer):
    """One booking in the traveler's history (US-06)."""

    storage_point = BookingStoragePointSerializer(read_only=True)
    qr = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            "id", "storage_point", "drop_off_at", "pick_up_at", "bags_count",
            "total_price", "status", "created_at", "qr",
        )
        read_only_fields = fields

    def get_qr(self, booking):
        # Completed or cancelled bookings have no active QR code.
        if not has_active_qr(booking):
            return None
        url = qr_url(booking)
        return {
            "token": booking.qr_token,
            "url": url,
            "image": qr_svg_data_uri(url),
        }
