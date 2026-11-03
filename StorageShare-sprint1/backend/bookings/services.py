"""Price, opening hours and capacity rules for creating a booking."""

from datetime import datetime, time, timedelta, timezone as datetime_timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from accounts.models import User
from bookings.models import Booking, BookingStatus
from storage.models import StoragePoint


CAPACITY_STATUSES = (
    BookingStatus.AWAITING_PAYMENT,
    BookingStatus.CONFIRMED,
    BookingStatus.CHECKED_IN,
)


def validate_booking_times(drop_off_at: datetime, pick_up_at: datetime) -> None:
    if drop_off_at <= timezone.now():
        raise ValidationError({"drop_off_at": "Drop-off must be in the future."})
    if pick_up_at <= drop_off_at:
        raise ValidationError({"pick_up_at": "Pick-up must be after drop-off."})


def calculate_total_price(
    hourly_price: Decimal,
    bags_count: int,
    drop_off_at: datetime,
    pick_up_at: datetime,
) -> Decimal:
    # UTC gives elapsed time even when the input offsets are different.
    duration = (
        pick_up_at.astimezone(datetime_timezone.utc)
        - drop_off_at.astimezone(datetime_timezone.utc)
    )
    microseconds = duration // timedelta(microseconds=1)
    with localcontext() as context:
        context.prec = 40
        total = (
            hourly_price * bags_count * Decimal(microseconds)
            / Decimal("3600000000")
        )
        total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if total > Decimal("9999999999.99"):
        raise ValidationError({"pick_up_at": "The total price is too large."})
    return total


def is_open_at(
    value: time, opens_at: time, closes_at: time, *, is_drop_off: bool
) -> bool:
    # Equal opening and closing times represent a 24-hour point.
    if opens_at == closes_at:
        return True
    if value == closes_at:
        return not is_drop_off
    if opens_at < closes_at:
        return opens_at <= value < closes_at
    # For example, a point open from 20:00 until 06:00.
    return value >= opens_at or value < closes_at


def validate_opening_hours(
    point: StoragePoint, drop_off_at: datetime, pick_up_at: datetime
) -> None:
    local_zone = ZoneInfo(settings.TIME_ZONE)
    for name, value, is_drop_off in (
        ("drop_off_at", drop_off_at, True),
        ("pick_up_at", pick_up_at, False),
    ):
        local_time = timezone.localtime(value, local_zone).time()
        if not is_open_at(
            local_time, point.opens_at, point.closes_at,
            is_drop_off=is_drop_off,
        ):
            raise ValidationError({
                name: "This time is outside the storage point's opening hours."
            })


def available_capacity(
    point: StoragePoint, drop_off_at: datetime, pick_up_at: datetime
) -> int:
    """Call while holding the storage point's row lock."""
    overlaps = Booking.objects.filter(
        storage_point=point,
        status__in=CAPACITY_STATUSES,
        drop_off_at__lt=pick_up_at,
        pick_up_at__gt=drop_off_at,
    ).values_list("drop_off_at", "pick_up_at", "bags_count")

    events = []
    for start, end, count in overlaps:
        events.append((max(start, drop_off_at), count))
        events.append((min(end, pick_up_at), -count))

    occupied = 0
    peak = 0
    # Negative changes come first at the same time: pick-up frees the space.
    for moment, change in sorted(events):
        occupied += change
        peak = max(peak, occupied)
    return max(0, point.capacity_bags - peak)


@transaction.atomic
def create_booking(
    *,
    traveler: User,
    storage_point: StoragePoint,
    drop_off_at: datetime,
    pick_up_at: datetime,
    bags_count: int,
) -> Booking:
    if not traveler.is_authenticated or not traveler.is_traveler:
        raise PermissionDenied("Only travelers can create bookings.")
    if type(bags_count) is not int or not 1 <= bags_count <= 32767:
        raise ValidationError({"bags_count": "Enter a whole number from 1 to 32767."})

    try:
        # Lock the point, including when it has no bookings yet. Other requests
        # for this point wait until this whole transaction has finished.
        point = StoragePoint.objects.select_for_update().get(
            pk=storage_point.pk, is_active=True,
        )
    except StoragePoint.DoesNotExist:
        raise ValidationError({"storage_point": "This storage point is unavailable."})

    # Recheck after waiting for the lock, using the current point and time.
    validate_booking_times(drop_off_at, pick_up_at)
    validate_opening_hours(point, drop_off_at, pick_up_at)
    available = available_capacity(point, drop_off_at, pick_up_at)
    if bags_count > available:
        raise ValidationError({
            "bags_count": (
                f"Not enough capacity. Available for this interval: {available} bag(s)."
            )
        })

    total_price = calculate_total_price(
        point.price_per_bag_per_hour, bags_count, drop_off_at, pick_up_at,
    )
    return Booking.objects.create(
        traveler=traveler,
        storage_point=point,
        drop_off_at=drop_off_at,
        pick_up_at=pick_up_at,
        bags_count=bags_count,
        total_price=total_price,
        status=BookingStatus.AWAITING_PAYMENT,
    )
