"""QR codes for bookings. The code encodes a link with the booking's random token."""

import segno
from django.conf import settings

from bookings.models import Booking, BookingStatus

# A partner can still check in or hand back luggage for these bookings.
QR_ACTIVE_STATUSES = (BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN)


def has_active_qr(booking: Booking) -> bool:
    return booking.status in QR_ACTIVE_STATUSES


# The frontend route the partner's phone opens. Agreed for US-09.
QR_PATH = "/partner/check-in/{token}"


def qr_url(booking: Booking) -> str:
    return settings.FRONTEND_BASE_URL + QR_PATH.format(token=booking.qr_token)


def qr_svg_data_uri(url: str) -> str:
    """SVG image as a data URI, usable directly in <img src="...">."""
    return segno.make(url, error="m").svg_data_uri(scale=4, border=2)
