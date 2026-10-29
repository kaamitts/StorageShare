# Storage points API — US-02 (list and district filter) and US-03 (detail page)

Base URL in development: `http://localhost:8000/api/`
All endpoints require `Authorization: Bearer <access>` — US-02 starts with
"I am logged in".

---

## GET /api/storage-points/

Returns the active storage points as cards. With `?district=` only the points
of that district, without it the whole active list.

The card deliberately carries only name, district and price — the rest of the
fields live on the detail endpoint below.

**Request**

```
GET /api/storage-points/?district=medeu
Authorization: Bearer <access token>
```

**200 OK**

```json
[
  {
    "id": 1,
    "name": "Almaty Hostel — reception",
    "district": "Medeu",
    "district_code": "medeu",
    "price_per_bag_per_hour": "300.00"
  },
  {
    "id": 2,
    "name": "Cafe Centre — back room",
    "district": "Medeu",
    "district_code": "medeu",
    "price_per_bag_per_hour": "250.00"
  }
]
```

- `district` is the label to print on the card, `district_code` is the value to
  send back in the filter.
- `price_per_bag_per_hour` is a string, in KZT. It is a decimal, so it is sent
  as a string to avoid rounding errors in JavaScript — use it as text on the
  card, and parse it only when you need arithmetic.
- The list is ordered by name, and inactive points are never returned.
- The card carries nothing else on purpose: address, opening hours, capacity
  and security notes belong to the detail page (US-03).

**200 OK, empty district**

```json
[]
```

A valid district with no points returns an empty array, not an error. This is
the case behind the "No storage points in this district" message in US-02,
scenario 2.

**400 Bad Request, unknown district**

```json
{
  "district": [
    "\"narnia\" is not a valid district. Valid values: alatau, almaly, auezov, bostandyk, medeu, nauryzbai, turksib, zhetysu."
  ]
}
```

A district outside the fixed list is rejected instead of answered with an empty
list, so a typo in the frontend is visible instead of looking like "no points
here". The value is case-insensitive and trimmed, so `?district=MEDEU` works.

**401 Unauthorized** — `{"detail": "Authentication credentials were not provided."}`

---

## GET /api/storage-points/{id}/

The storage point page (US-03): everything a traveler needs before booking.

**Request**

```
GET /api/storage-points/1/
Authorization: Bearer <access token>
```

Use the trailing slash. Without it Django answers 301 to the same URL with the
slash; most clients follow it, but some drop the `Authorization` header on a
redirect and you get a confusing 401.

**200 OK**

```json
{
  "id": 1,
  "name": "Almaty Hostel — reception",
  "district": "Medeu",
  "district_code": "medeu",
  "address": "Dostyk ave 85",
  "opens_at": "08:00",
  "closes_at": "23:00",
  "security_notes": "Locked room behind the reception desk, camera.",
  "price_per_bag_per_hour": "300.00"
}
```

- `opens_at` and `closes_at` come as `"HH:MM"`, ready to print as
  `08:00 – 23:00`.
- `security_notes` can be an empty string — hide the block when it is.
- The `id` is the same one the card carries in the list, so the card links
  straight to `/storage-points/{id}/`.

**404 Not Found**

```json
{"detail": "No StoragePoint matches the given query."}
```

Returned both for an id that does not exist and for a point the partner has
deactivated. A hidden point is not in the list either, so the two endpoints
never disagree.

**401 Unauthorized** — no token, same as the list.

---

## GET /api/districts/

The fixed district list, so the filter control does not hard-code it.

**200 OK**

```json
[
  {"code": "alatau", "name": "Alatau"},
  {"code": "almaly", "name": "Almaly"},
  {"code": "auezov", "name": "Auezov"},
  {"code": "bostandyk", "name": "Bostandyk"},
  {"code": "medeu", "name": "Medeu"},
  {"code": "nauryzbai", "name": "Nauryzbai"},
  {"code": "turksib", "name": "Turksib"},
  {"code": "zhetysu", "name": "Zhetysu"}
]
```

Build the dropdown from `name`, send `code` as `?district=`.

---

## Notes for the frontend

```js
const districts = await api("/api/districts/");          // fill the dropdown
const cards = await api(`/api/storage-points/?district=${code}`);

if (cards.length === 0) {
  showMessage("No storage points in this district");
}
```

On a 400 the body always has the field name as the key, so the same error
handling as the auth forms works here.

---

## Model

`StoragePoint` lives in `backend/storage/models.py`:

| Field | Type | Notes |
| --- | --- | --- |
| `partner` | FK → `users` | `ON DELETE RESTRICT`; only accounts with `role = partner` |
| `name` | varchar(120) | shown on the card |
| `address` | varchar(255) | detail page only |
| `district` | varchar(32) | fixed list, indexed |
| `price_per_bag_per_hour` | numeric(8,2) | `CHECK >= 0` |
| `capacity_bags` | smallint | `CHECK > 0`; used by the booking check in US-04 |
| `opens_at`, `closes_at` | time | detail page only |
| `security_notes` | text | detail page only |
| `is_active` | boolean | a partner hides a point instead of deleting it |
| `created_at`, `updated_at` | timestamptz | |

Index on `(district, is_active)` — every list query starts with those two
columns. The district check constraint repeats the fixed list in the database,
because `choices` is only enforced by forms and serializers.
