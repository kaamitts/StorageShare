# Booking history API and QR codes — US-06

Base URL in development: `http://localhost:8000/api/`
Requires `Authorization: Bearer <access>` of a **traveler**.

---

## GET /api/bookings/history/

Returns the current traveler's own bookings, newest drop-off first.

- Only bookings of the logged-in traveler; other travelers' bookings never appear.
- Bookings in `awaiting_payment` are excluded. They appear after the mock
  payment (`POST /api/bookings/<id>/pay/`, US-05).
- `confirmed` and `checked_in` bookings carry a `qr` object.
- `completed` and `cancelled` bookings are listed with `"qr": null`.

**200 OK**

```json
[
  {
    "id": 12,
    "storage_point": {
      "id": 1,
      "name": "Almaty Hostel — reception",
      "address": "Abay ave 10",
      "district": "Medeu"
    },
    "drop_off_at": "2026-11-12T10:00:00+05:00",
    "pick_up_at": "2026-11-12T12:00:00+05:00",
    "bags_count": 2,
    "total_price": "1200.00",
    "status": "confirmed",
    "created_at": "2026-11-10T09:30:00+05:00",
    "qr": {
      "token": "q3Zk9yX1v0b2N_7pR8sT4uW6aC5dE0fG1hJ2kL3mN4o",
      "url": "http://localhost:5173/partner/check-in/q3Zk9yX1v0b2N_7pR8sT4uW6aC5dE0fG1hJ2kL3mN4o",
      "image": "data:image/svg+xml;charset=utf-8,%3Csvg..."
    }
  }
]
```

`qr.image` can be used directly: `<img src={booking.qr.image} alt="Booking QR" />`.

**Errors**

| Code | When |
|---|---|
| 401 | No or invalid token |
| 403 | The user is a partner |

---

## QR token rules

- `qr_token` is generated once when the booking is created
  (`secrets.token_urlsafe(32)`, 256 random bits) and never changes, so a
  booking always shows the same QR code.
- It is unique in the database and is not related to the sequential booking id.
- The API shows it only while the booking is `confirmed` or `checked_in`.

## QR link format (agreement for US-09)

```
<BOOKING_QR_URL_TEMPLATE with {token} replaced>
default: http://localhost:5173/partner/check-in/{token}
```

The template is set by the `BOOKING_QR_URL_TEMPLATE` environment variable and
must contain `{token}`. In production it points at the real frontend domain.

Proposed US-09 partner flow:

1. The partner, logged in, scans the QR. The phone opens
   `/partner/check-in/<token>` in the frontend.
2. The frontend takes `<token>` from the path and calls the partner API
   (to be built in US-09), for example `POST /api/partner/check-in/` with
   `{"token": "<token>"}`.
3. The backend finds the booking by `qr_token`, checks that it belongs to one of
   this partner's storage points, then moves `confirmed → checked_in` (drop-off)
   or `checked_in → completed` (pick-up).

The token alone does not grant anything: the partner must be authenticated and
own the storage point. A `completed` booking no longer gets a QR in the history,
and US-09 should reject its token.
