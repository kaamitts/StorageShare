from django.contrib.auth import get_user_model
from rest_framework import serializers

from bookings.models import Booking
from storage.models import StoragePoint

User = get_user_model()


class AdminBookingSerializer(serializers.ModelSerializer):
    traveler_name = serializers.SerializerMethodField()
    traveler_email = serializers.EmailField(source="traveler.email", read_only=True)
    traveler_phone = serializers.CharField(source="traveler.phone", read_only=True)
    storage_point_id = serializers.IntegerField(read_only=True)
    storage_point_name = serializers.CharField(source="storage_point.name", read_only=True)
    storage_point_address = serializers.CharField(source="storage_point.address", read_only=True)
    district = serializers.CharField(source="storage_point.get_district_display", read_only=True)

    class Meta:
        model = Booking
        fields = (
            "id", "traveler_name", "traveler_email", "traveler_phone",
            "storage_point_id", "storage_point_name", "storage_point_address",
            "district", "drop_off_at", "pick_up_at", "bags_count", "total_price",
            "status", "payment_expires_at", "checked_in_at", "checked_out_at",
            "created_at",
        )
        read_only_fields = fields

    def get_traveler_name(self, booking):
        return booking.traveler.full_name or booking.traveler.email


class AdminStoragePointSerializer(serializers.ModelSerializer):
    partner_email = serializers.EmailField(source="partner.email", read_only=True)
    partner_name = serializers.CharField(source="partner.full_name", read_only=True)
    district_name = serializers.CharField(source="get_district_display", read_only=True)
    bookings_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = StoragePoint
        fields = (
            "id", "name", "address", "district", "district_name",
            "price_per_bag_per_hour", "capacity_bags", "is_24_hours", "opens_at",
            "closes_at", "is_active", "partner_email", "partner_name",
            "bookings_count", "created_at",
        )
        read_only_fields = fields


class AdminUserSerializer(serializers.ModelSerializer):
    bookings_count = serializers.IntegerField(read_only=True)
    storage_points_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "email", "full_name", "phone", "role", "is_active",
            "created_at", "last_login", "bookings_count", "storage_points_count",
        )
        read_only_fields = fields


class ActiveStateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()
