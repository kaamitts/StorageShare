import math

from django.utils import timezone
from rest_framework import serializers

from bookings.models import Booking, BookingStatus
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
    traveler_booking_number = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id", "storage_point", "drop_off_at", "pick_up_at", "bags_count",
            "total_price", "status", "created_at", "qr", "traveler_booking_number",
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


class PendingBookingSerializer(serializers.ModelSerializer):
    storage_point = BookingStoragePointSerializer(read_only=True)
    payment_seconds_remaining = serializers.SerializerMethodField()
    traveler_booking_number = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id", "storage_point", "drop_off_at", "pick_up_at", "bags_count",
            "total_price", "status", "created_at", "payment_expires_at",
            "payment_seconds_remaining", "traveler_booking_number",
        )
        read_only_fields = fields

    def get_payment_seconds_remaining(self, booking):
        return max(
            0,
            math.ceil((booking.payment_expires_at - timezone.now()).total_seconds()),
        )


class PartnerBookingSerializer(serializers.ModelSerializer):
    """One booking in the partner's list (US-08)."""

    storage_point_id = serializers.IntegerField(read_only=True)
    storage_point_name = serializers.CharField(source="storage_point.name", read_only=True)
    point_booking_number = serializers.IntegerField(read_only=True)
    traveler_name = serializers.SerializerMethodField()
    traveler_email = serializers.EmailField(source="traveler.email", read_only=True)
    traveler_phone = serializers.CharField(source="traveler.phone", read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id", "storage_point_id", "storage_point_name", "drop_off_at",
            "pick_up_at", "bags_count", "status", "checked_in_at", "checked_out_at",
            "point_booking_number", "traveler_name", "traveler_email", "traveler_phone",
        )
        read_only_fields = fields

    def get_traveler_name(self, booking):
        return booking.traveler.full_name or booking.traveler.email


class PartnerCheckInSerializer(serializers.ModelSerializer):
    """The partner's check-in page opened from the QR link (US-09)."""

    storage_point = BookingStoragePointSerializer(read_only=True)
    traveler_name = serializers.SerializerMethodField()
    can_check_in = serializers.SerializerMethodField()
    can_check_out = serializers.SerializerMethodField()
    point_booking_number = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id", "storage_point", "traveler_name", "drop_off_at", "pick_up_at",
            "bags_count", "total_price", "status", "checked_in_at",
            "checked_out_at", "can_check_in", "can_check_out",
            "point_booking_number",
        )
        read_only_fields = fields

    def get_traveler_name(self, booking):
        return booking.traveler.full_name or booking.traveler.email

    def get_can_check_in(self, booking):
        return booking.status == BookingStatus.CONFIRMED

    def get_can_check_out(self, booking):
        return booking.status == BookingStatus.CHECKED_IN
