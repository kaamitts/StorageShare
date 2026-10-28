# Frontend integration notes — mock API vs the real backend

Written after comparing `frontend/src/api/auth.js` and `frontend/src/api/storage.js`
on branch `feat/IPM-9-auth-pages` with the backend built for IPM-8, IPM-12 and IPM-15.

The mocks were written before the grooming session of 12 October, so a few
things have moved. Six differences, in the order they will bite.

---

## 1. Login returns `access` and `refresh`, not `token`

**Mock**

```js
return { token: 'mock-token', user: {...} };
```

**Real response**

```json
{
  "user": { "id": 1, "email": "...", "full_name": "...", "role": "traveler" },
  "access":  "eyJhbGciOi...",
  "refresh": "eyJhbGciOi..."
}
```

`access` is the one to put in the header:
`Authorization: Bearer ${access}`. It expires after 30 minutes; `refresh` buys a
new one from `POST /api/auth/refresh/` and lives 7 days. Store both.

## 2. A taken email returns 400, not 409

**Mock** throws `{ status: 409 }`.

**Real response** is `400` with the field name as the key, the same shape as
every other validation error:

```json
{"email": ["A user with this email already exists."]}
```

So one error handler covers taken email, weak password and bad role.

## 3. Price is per hour, not per day

**Mock** has `price_per_bag_per_day: 500`.

The grooming session of 12 October decided **per hour**, and TSIS 6–7 is built
on that: total price = price per bag per hour × bags × hours. The field is
`price_per_bag_per_hour`.

It also comes as a **string**, not a number:

```json
"price_per_bag_per_hour": "300.00"
```

It is a decimal, and sending it as a JSON number would let JavaScript round it
in the US-04 total. Print it as text; parse it only for arithmetic.

> `docs/db-schema.md` still says `price_per_bag_per_day` — that line is out of
> date and should be fixed on the schema branch.

## 4. District is a plain code plus a label, not a `{kk, ru, en}` object

**Mock**

```js
district: { kk: 'Алмалы', ru: 'Алмалинский', en: 'Alatau' }
```

**Real response**

```json
"district": "Medeu",
"district_code": "medeu"
```

`district_code` is what you send back as `?district=`; `district` is the label.
The backend stores one fixed code per district and does not hold translations —
if the UI stays trilingual, keep the kk/ru/en labels in the frontend and key
them by `district_code`.

Also note the mock maps `Алмалы → 'Alatau'`: Almaly and Alatau are two different
districts. The real list has all eight:

```
alatau, almaly, auezov, bostandyk, medeu, nauryzbai, turksib, zhetysu
```

`GET /api/districts/` returns them as `{code, name}` so the dropdown does not
have to hard-code anything.

## 5. Opening hours come as two fields

**Mock** has `open_hours: '08:00–22:00'`.

**Real response** has `"opens_at": "08:00"` and `"closes_at": "23:00"`, already
without seconds. Join them in the component:
`` `${opens_at} – ${closes_at}` ``.

## 6. `area_m2` and `phone` on a storage point do not exist

Neither is in the agreed schema and neither appears in any Must feature, so the
backend does not return them. The detail endpoint returns exactly: `id`, `name`,
`district`, `district_code`, `address`, `opens_at`, `closes_at`,
`security_notes`, `price_per_bag_per_hour`.

`security_notes` can be an empty string — hide the block instead of printing an
empty heading.

---

## One more thing: the role value is `traveler`, with one "l"

`docs/db-schema.md` and the mock both use `traveler`, so the backend stores
`traveler`. The TSIS 6–7 document spells it "traveller" in prose, but that is
prose, not a stored value. One letter, and it would have cost an afternoon of
debugging, so it is worth saying out loud at the next call.

## Endpoints, in one place

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| POST | `/api/auth/register/` | no | register, returns user + tokens |
| POST | `/api/auth/login/` | no | log in, returns user + tokens |
| POST | `/api/auth/refresh/` | no | new access token |
| POST | `/api/auth/logout/` | yes | blacklist the refresh token |
| GET | `/api/auth/me/` | yes | the logged-in user |
| GET | `/api/districts/` | yes | the fixed district list |
| GET | `/api/storage-points/?district=` | yes | result cards |
| GET | `/api/storage-points/{id}/` | yes | the storage point page |

Full request and response examples: `docs/api-auth.md` and
`docs/api-storage-points.md`.
