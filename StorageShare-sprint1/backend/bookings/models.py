import secrets

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class BookingStatus(models.TextChoices):
    AWAITING_PAYMENT = "awaiting_payment", "Awaiting payment"
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

    # Set once when the booking is created and never changed, so the QR code
    # of a booking stays the same. It is shown only while the booking is active.
    qr_token = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        default=generate_qr_token,
    )

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