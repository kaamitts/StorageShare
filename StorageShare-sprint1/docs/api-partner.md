# Partner API — Sprint 3 (US-07, US-08, US-09)

Base URL in development: `http://localhost:8000/api/`
Partner-only endpoints require `Authorization: Bearer <access>` of a **partner**
(`role = "partner"`). A traveler gets `403`, no token gets `401`.

---

## US-07 · POST /api/storage-points/

Creates a storage point owned by the logged-in partner. The partner is always
taken from the token; a `partner` or `is_active` value in the body is ignored.
`GET /api/storage-points/` stays open to every logged-in user.

**Request**

```json
{
  "name": "Hostel Almaty — reception",
  "address": "Abay ave 10",
  "district": "medeu",
  "price_per_bag_per_hour": "300.00",
  "capacity_bags": 10,
  "opens_at": "08:00",
  "closes_at": "22:00",
  "security_notes": "CCTV, locked room"
}
```

`security_notes` is optional. `district` is a code from `GET /api/districts/`.

**201 Created**

```json
{
  "id": 7,
  "partner": 3,
  "name": "Hostel Almaty — reception",
  "address": "Abay ave 10",
  "district": "medeu",
  "price_per_bag_per_hour": "300.00",
  "capacity_bags": 10,
  "opens_at": "08:00",
  "closes_at": "22:00",
  "security_notes": "CCTV, locked room",
  "is_active": true,
  "created_at": "2026-11-16T10:00:00+05:00"
}
```

The point immediately appears in `GET /api/storage-points/?district=medeu`.

**400 Bad Request** — the key is the field name:

| Input | Response |
|---|---|
| empty / missing / negative price | `{"price_per_bag_per_hour": [...]}` |
| capacity `0`, negative or empty | `{"capacity_bags": ["Ensure this value is greater than or equal to 1."]}` |
| unknown district | `{"district": ["\"downtown\" is not a valid choice."]}` |
| closing time not later than opening | `{"closes_at": ["Closing time must be later than opening time."]}` |
| empty name / address | `{"name": [...], "address": [...]}` |

The form and endpoint support ordinary, overnight, and 24-hour schedules.
For 24-hour points the stored opening and closing times are both `00:00`; use
`is_24_hours` to distinguish them from an ordinary schedule.

---

## Partner storage points · GET /api/partner/storage-points/

Returns every storage point owned by the logged-in partner, including inactive
points. Results are scoped to the authenticated user and ordered by point name.
The response includes `district` and `district_code`, address, opening and
closing times, `is_24_hours`, and `is_active`. Times use `HH:MM`; a 24/7 point
still includes its stored time values, while `is_24_hours` determines display.

The endpoint requires a partner access token. Requests without a valid token
return `401`; authenticated users without the partner role receive `403`.

### DELETE /api/partner/storage-points/<id>/

Permanently deletes an unbooked point owned by the authenticated partner. Returns
`204 No Content`. A point with booking history is preserved and returns `409`
so booking records remain valid. A point owned by another partner returns `404`.

---

## US-08 · GET /api/partner/bookings/

The bookings of the logged-in partner's own storage points, ordered by drop-off
time. Bookings still `awaiting_payment` are not returned. Another partner's
bookings never appear. An empty list means "No bookings yet".

**200 OK**

```json
[
  {
    "id": 12,
    "storage_point_id": 7,
    "storage_point_name": "Hostel Almaty — reception",
    "drop_off_at": "2026-11-18T10:00:00+05:00",
    "pick_up_at": "2026-11-18T12:00:00+05:00",
    "bags_count": 2,
    "status": "confirmed",
    "checked_in_at": null,
    "checked_out_at": null
  }
]
```

---

## US-09 · Check-in and check-out by QR token

### QR link

The traveler's History (`GET /api/bookings/history/`) returns `qr.url`:

```
<FRONTEND_BASE_URL>/partner/check-in/<qr_token>
```

The partner opens it with the phone camera. The frontend page takes `<qr_token>`
from the path and calls the endpoints below. The token is a random 43-character
URL-safe string (`secrets.token_urlsafe(32)`), not the booking id and not a UUID.

### GET /api/bookings/by-token/<qr_token>/

The data for the check-in page.

```json
{
  "id": 12,
  "storage_point": {"id": 7, "name": "Hostel Almaty — reception", "address": "Abay ave 10", "district": "Medeu"},
  "traveler_name": "Aigerim S.",
  "drop_off_at": "2026-11-18T10:00:00+05:00",
  "pick_up_at": "2026-11-18T12:00:00+05:00",
  "bags_count": 2,
  "total_price": "1200.00",
  "status": "confirmed",
  "checked_in_at": null,
  "checked_out_at": null,
  "can_check_in": true,
  "can_check_out": false
}
```

Use `can_check_in` / `can_check_out` to show the right button.

### POST /api/bookings/by-token/<qr_token>/check-in/

`confirmed → checked_in`, saves `checked_in_at`. Returns the same object as the GET.

### POST /api/bookings/by-token/<qr_token>/check-out/

`checked_in → completed`, saves `checked_out_at`. After this the traveler's History
returns `"qr": null` for the booking.

### Errors

| Code | When | `detail` |
|---|---|---|
| 401 | No or invalid token | — |
| 403 | Traveler | `Only partners can do this.` |
| 403 | Partner of another storage point | `This booking belongs to another partner's storage point.` |
| 404 | Unknown QR token | `No booking found for this QR code.` |
| 409 | Unpaid booking | `This booking has not been paid yet.` |
| 409 | Check-in twice | `The bags are already checked in.` |
| 409 | Check-out before check-in | `The bags must be checked in before check-out.` |
| 409 | Check-out twice | `The bags are already checked out.` |
| 409 | Check-in on a completed booking | `This booking is already completed.` |
| 409 | Cancelled booking | `This booking was cancelled.` |

Each change runs in a transaction with a row lock on the booking, so two scans at
the same moment change the status once; the second gets `409`.

### Opening the QR link from a phone on the same Wi-Fi

1. Find the computer's LAN IP (`ipconfig` → IPv4, e.g. `192.168.1.20`).
2. **Vite dev server:** run the frontend with `npm run dev -- --host`, and start the
   backend with `FRONTEND_BASE_URL=http://192.168.1.20:5173` and
   `ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.20` (the Vite proxy keeps the
   phone's Host header).
   **Docker:** in `.env` next to `docker-compose.yml` set

   ```
   FRONTEND_BIND=0.0.0.0
   FRONTEND_BASE_URL=http://192.168.1.20:8080
   ALLOWED_HOSTS=localhost,127.0.0.1,backend,192.168.1.20
   ```

3. Allow the port through the Windows firewall if the phone cannot connect.
4. Already created bookings pick up the new address automatically: the URL is
   built from the setting each time, only the token is stored.
