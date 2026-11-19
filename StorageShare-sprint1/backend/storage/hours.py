"""Shared opening-hours rules for booking validation and storage discovery."""

from datetime import datetime, time
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone


def is_open_at(
    value: time, opens_at: time, closes_at: time, *, is_drop_off: bool
) -> bool:
    """Return whether a handover at ``value`` is allowed by the daily schedule."""
    # Equal values are the legacy representation of all-day opening.
    if opens_at == closes_at:
        return True
    # A pick-up may happen at closing; a drop-off must happen before it.
    if value == closes_at:
        return not is_drop_off
    if opens_at < closes_at:
        return opens_at <= value < closes_at
    # Overnight interval, for example 20:00–02:00.
    return value >= opens_at or value < closes_at


def storage_point_is_open(point, at: datetime | None = None) -> bool:
    """Check a point at an aware instant, using the project's local timezone."""
    if point.is_24_hours:
        return True
    instant = at or timezone.now()
    local_time = timezone.localtime(instant, ZoneInfo(settings.TIME_ZONE)).time()
    # For discovery, the closing boundary is closed (same as drop-off rules).
    return is_open_at(
        local_time, point.opens_at, point.closes_at, is_drop_off=True,
    )
