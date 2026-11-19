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

## QR link format (used by US-09)

```
<FRONTEND_BASE_URL>/partner/check-in/<qr_token>
default: http://localhost:5173/partner/check-in/<qr_token>
```

`FRONTEND_BASE_URL` is an environment variable. In production it points at the
real frontend domain; for a phone on the same Wi-Fi it uses the computer's LAN IP.
The partner flow that opens this link is described in [api-partner.md](api-partner.md).
