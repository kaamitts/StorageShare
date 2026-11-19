import secrets
from datetime import timedelta

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


PAYMENT_RESERVATION_DURATION = timedelta(minutes=15)


def default_payment_expires_at():
    return timezone.now() + PAYMENT_RESERVATION_DURATION


class BookingStatus(models.TextChoices):
    AWAITING_PAYMENT = "awaiting_payment", "Awaiting payment"
    EXPIRED = "expired", "Expired"
    CONFIRMED = "confirmed", "Confirmed"
    CHECKED_IN = "checked_in", "Checked in"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


def generate_qr_token() -> str:
    """Unpredictable token for the QR link (256 random bits, URL-safe)."""
    return secrets.token_urlsafe(32)


class Booking(models.Model):
    traveler = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    storage_point = models.ForeignKey(
        "storage.StoragePoint",
        on_delete=models.PROTECT,
        related_name="bookings",
    )

    drop_off_at = models.DateTimeField()
    pick_up_at = models.DateTimeField()

    bags_count = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
    )

    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    status = models.CharField(
        max_length=20,
        choices=BookingStatus.choices,
        default=BookingStatus.AWAITING_PAYMENT,
    )

    payment_expires_at = models.DateTimeField(default=default_payment_expires_at)

    # Set once when the booking is created and never changed, so the QR code
    # of a booking stays the same. It is shown only while the booking is active.
    qr_token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        default=generate_qr_token,
    )

    # Set by the partner's QR scan (US-09).
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        ordering = ["-created_at"]

        indexes = [
            models.Index(
                fields=["storage_point", "drop_off_at", "pick_up_at"],
                name="booking_point_times_idx",
            ),
            models.Index(
                fields=["status", "payment_expires_at"],
                name="booking_status_expiry_idx",
            ),
        ]

        constraints = [
            models.CheckConstraint(
                condition=models.Q(bags_count__gt=0),
                name="booking_bags_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    pick_up_at__gt=models.F("drop_off_at")
                ),
                name="booking_pickup_after_dropoff",
            ),
            models.CheckConstraint(
                condition=models.Q(total_price__gte=0),
                name="booking_price_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=BookingStatus.values),
                name="booking_status_valid",
            ),
        ]

    def __str__(self) -> str:
        return f"Booking #{self.pk} — storage point #{self.storage_point_id}"
