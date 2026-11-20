"""Booking rules: price, opening hours, capacity and mock payment."""

from datetime import datetime, timedelta, timezone as datetime_timezone
from decimal import Decimal, ROUND_HALF_UP, localcontext
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.db.models import Count, OuterRef, Q, Subquery
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import (
    APIException, NotFound, PermissionDenied, ValidationError,
)

from accounts.models import User
from bookings.models import (
    PAYMENT_RESERVATION_DURATION,
    Booking,
    BookingStatus,
)
from storage.hours import is_open_at
from storage.models import StoragePoint


class BookingConflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "The booking cannot change to this status."
    default_code = "booking_conflict"


class BookingPaymentExpired(BookingConflict):
    default_detail = "The 15-minute payment window has expired."
    default_code = "booking_payment_expired"


class PendingBookingExists(BookingConflict):
    default_detail = "You already have a booking awaiting payment."
    default_code = "pending_booking_exists"


class BookingCancellationNotAllowed(BookingConflict):
    default_detail = "Only bookings awaiting payment can be cancelled here."
    default_code = "booking_cancellation_not_allowed"


CAPACITY_STATUSES = (
    BookingStatus.CONFIRMED,
    BookingStatus.CHECKED_IN,
)


def booking_sequence_number(scope_field: str) -> Subquery:
    """Return a stable 1-based booking number within a traveler or storage point."""
    earlier_bookings = (
        Booking.objects.filter(**{scope_field: OuterRef(scope_field)})
        .filter(
            Q(created_at__lt=OuterRef("created_at"))
            | Q(created_at=OuterRef("created_at"), pk__lte=OuterRef("pk"))
        )
        .order_by()
        .values(scope_field)
        .annotate(sequence=Count("pk"))
        .values("sequence")[:1]
    )
    return Subquery(earlier_bookings)


def payment_deadline_passed(expires_at, *, now=None) -> bool:
    """The single boundary rule used by payment and the expiry sweeper."""
    return expires_at <= (now or timezone.now())


def expired_payment_filter(*, now=None) -> Q:
    """ORM equivalent of payment_deadline_passed for set-based queries."""
    return Q(payment_expires_at__lte=now or timezone.now())


def expire_pending_bookings(*, now=None) -> int:
    """Mark all unpaid reservations whose 15-minute window has elapsed."""
    now = now or timezone.now()
    return Booking.objects.filter(
        status=BookingStatus.AWAITING_PAYMENT,
    ).filter(
        expired_payment_filter(now=now),
    ).update(status=BookingStatus.EXPIRED, updated_at=now)


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


def validate_opening_hours(
    point: StoragePoint, drop_off_at: datetime, pick_up_at: datetime
) -> None:
    if point.is_24_hours:
        return

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
    now = timezone.now()
    overlaps = Booking.objects.filter(
        storage_point=point,
    ).filter(
        Q(status__in=CAPACITY_STATUSES)
        | (
            Q(status=BookingStatus.AWAITING_PAYMENT)
            & ~expired_payment_filter(now=now)
        ),
    ).filter(
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

    # Serialize booking creation per traveler, including bookings for different
    # storage points, so concurrent requests cannot create multiple reservations.
    User.objects.select_for_update().get(pk=traveler.pk)
    now = timezone.now()
    if Booking.objects.filter(
        traveler=traveler,
        status=BookingStatus.AWAITING_PAYMENT,
        payment_expires_at__gt=now,
    ).exists():
        raise PendingBookingExists()

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
    booking = Booking.objects.create(
        traveler=traveler,
        storage_point=point,
        drop_off_at=drop_off_at,
        pick_up_at=pick_up_at,
        bags_count=bags_count,
        total_price=total_price,
        status=BookingStatus.AWAITING_PAYMENT,
    )
    # Use the persisted creation timestamp as the exact start of the reservation.
    booking.payment_expires_at = booking.created_at + PAYMENT_RESERVATION_DURATION
    Booking.objects.filter(pk=booking.pk).update(
        payment_expires_at=booking.payment_expires_at,
    )
    return booking


# Statuses that a successful payment has already reached or passed.
PAID_STATUSES = (
    BookingStatus.CONFIRMED,
    BookingStatus.CHECKED_IN,
    BookingStatus.COMPLETED,
)


def confirm_booking_payment(*, user: User, booking_id: int) -> tuple[Booking, bool]:
    """Mock payment: move the owner's booking from awaiting payment to confirmed.

    Returns the booking and whether this call changed its status. Repeated
    calls are safe: a booking that is already paid is returned unchanged, so a
    later status such as checked in is never reset. The total price is never
    recalculated.
    """
    # Lock the row so two simultaneous payments perform only one transition.
    # Filtering by owner makes another user's booking look like it does not exist.
    expired = False
    with transaction.atomic():
        # Locking serializes payment with the expiry worker and other pay calls.
        booking = (
            Booking.objects.select_for_update()
            .filter(pk=booking_id, traveler_id=user.pk)
            .first()
        )
        if booking is None:
            raise NotFound("Booking not found.")

        if booking.status == BookingStatus.AWAITING_PAYMENT:
            now = timezone.now()
            if payment_deadline_passed(booking.payment_expires_at, now=now):
                booking.status = BookingStatus.EXPIRED
                booking.save(update_fields=["status", "updated_at"])
                expired = True
            else:
                booking.status = BookingStatus.CONFIRMED
                booking.save(update_fields=["status", "updated_at"])
                return booking, True
        elif booking.status in PAID_STATUSES:
            return booking, False
        elif booking.status == BookingStatus.EXPIRED:
            raise BookingPaymentExpired()
        else:
            raise BookingConflict(
                f"A booking with status '{booking.status}' cannot be paid."
            )

    # Raise only after the transaction commits so the expired status persists.
    if expired:
        raise BookingPaymentExpired()
    raise AssertionError("Unexpected booking payment state.")


def cancel_pending_booking(*, user: User, booking_id: int) -> tuple[Booking, bool]:
    """Cancel an unpaid reservation; paid bookings need a separate refund flow."""
    with transaction.atomic():
        booking = (
            Booking.objects.select_for_update()
            .filter(pk=booking_id, traveler_id=user.pk)
            .first()
        )
        if booking is None:
            raise NotFound("Booking not found.")

        if booking.status == BookingStatus.CANCELLED:
            return booking, False
        if booking.status == BookingStatus.EXPIRED:
            return booking, False
        if booking.status != BookingStatus.AWAITING_PAYMENT:
            raise BookingCancellationNotAllowed()

        if payment_deadline_passed(booking.payment_expires_at):
            booking.status = BookingStatus.EXPIRED
        else:
            booking.status = BookingStatus.CANCELLED
        booking.save(update_fields=["status", "updated_at"])
        return booking, True


# US-09: partner check-in and check-out by the QR token.

def get_booking_for_partner(*, partner: User, token: str, lock: bool = False) -> Booking:
    """The booking behind a QR token, if it belongs to one of this partner's points.

    Unknown token -> 404. A booking of another partner's point -> 403.
    """
    queryset = Booking.objects.select_related("storage_point", "traveler").annotate(
        point_booking_number=booking_sequence_number("storage_point_id"),
    )
    if lock:
        # Lock only the booking row; select_related would also lock the joined rows.
        queryset = queryset.select_for_update(of=("self",))
    booking = queryset.filter(qr_token=token).first()
    if booking is None:
        raise NotFound("No booking found for this QR code.")
    if booking.storage_point.partner_id != partner.pk:
        raise PermissionDenied("This booking belongs to another partner's storage point.")
    return booking


CHECK_IN_ERRORS = {
    BookingStatus.AWAITING_PAYMENT: "This booking has not been paid yet.",
    BookingStatus.EXPIRED: "The payment period for this booking has expired.",
    BookingStatus.CHECKED_IN: "The bags are already checked in.",
    BookingStatus.COMPLETED: "This booking is already completed.",
    BookingStatus.CANCELLED: "This booking was cancelled.",
}

CHECK_OUT_ERRORS = {
    BookingStatus.AWAITING_PAYMENT: "This booking has not been paid yet.",
    BookingStatus.EXPIRED: "The payment period for this booking has expired.",
    BookingStatus.CONFIRMED: "The bags must be checked in before check-out.",
    BookingStatus.COMPLETED: "The bags are already checked out.",
    BookingStatus.CANCELLED: "This booking was cancelled.",
}


@transaction.atomic
def check_in_booking(*, partner: User, token: str) -> Booking:
    """confirmed -> checked_in, saving the time. Two scans at once change it once."""
    booking = get_booking_for_partner(partner=partner, token=token, lock=True)
    if booking.status != BookingStatus.CONFIRMED:
        raise BookingConflict(CHECK_IN_ERRORS[booking.status])
    booking.status = BookingStatus.CHECKED_IN
    booking.checked_in_at = timezone.now()
    booking.save(update_fields=["status", "checked_in_at", "updated_at"])
    return booking


@transaction.atomic
def check_out_booking(*, partner: User, token: str) -> Booking:
    """checked_in -> completed, saving the time. After this the QR is no longer shown."""
    booking = get_booking_for_partner(partner=partner, token=token, lock=True)
    if booking.status != BookingStatus.CHECKED_IN:
        raise BookingConflict(CHECK_OUT_ERRORS[booking.status])
    booking.status = BookingStatus.COMPLETED
    booking.checked_out_at = timezone.now()
    booking.save(update_fields=["status", "checked_out_at", "updated_at"])
    return booking
