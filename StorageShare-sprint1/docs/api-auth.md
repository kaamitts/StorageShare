# Auth API — US-01 (IPM-8)

Base URL in development: `http://localhost:8000/api/auth/`
Authentication: JWT. Protected requests send `Authorization: Bearer <access>`.
Access token lives 30 minutes, refresh token 7 days.

Roles: `traveler` and `partner`. The role is chosen at registration and cannot
be changed through the API.

---

## POST /api/auth/register/

Creates an account and signs the user in immediately, so the frontend does not
have to call login right after registration.

**Request**

```json
{
  "email": "aizhan@example.com",
  "password": "StorageShare2026",
  "full_name": "Aizhan T.",
  "phone": "+7 700 000 00 01",
  "role": "traveler"
}
```

`full_name` and `role` are required. `phone` is optional.
The role must be explicitly chosen: `traveler` or `partner`.

**201 Created**

```json
{
  "user": {
    "id": 1,
    "email": "aizhan@example.com",
    "full_name": "Aizhan T.",
    "phone": "",
    "role": "traveler",
    "created_at": "2026-10-14T21:00:00.232176+05:00"
  },
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**400 Bad Request** — the field name is the key, so the form can show the error
under the right input:

```json
{"email": ["A user with this email already exists."]}
{"password": ["This password is too common."]}
{"role": ["\"admin\" is not a valid choice."]}
```

Email is compared case-insensitively: `AIZHAN@example.com` and
`aizhan@example.com` are the same account, and the address is stored lowercase.

---

## POST /api/auth/login/

**Request**

```json
{"email": "aizhan@example.com", "password": "StorageShare2026"}
```

**200 OK** — same shape as registration: `user`, `access`, `refresh`.

**401 Unauthorized**

```json
{"detail": "Invalid email or password."}
```

The same message is returned for an unknown email, a wrong password and a
disabled account, so the endpoint cannot be used to find out which emails are
registered.

---

## POST /api/auth/refresh/

```json
{"refresh": "<refresh token>"}
```

**200 OK** returns a new `access` and, because refresh rotation is on, a new
`refresh`. The old refresh token stops working, so store the new one.

**401 Unauthorized** if the token is expired, invalid or blacklisted.

---

## GET /api/auth/me/

Requires `Authorization: Bearer <access>`. Use it on page reload to restore the
session from a stored token.

**200 OK**

```json
{
  "id": 1,
  "email": "aizhan@example.com",
  "full_name": "Aizhan T.",
  "phone": "",
  "role": "traveler",
  "created_at": "2026-10-14T21:00:00.232176+05:00"
}
```

**401 Unauthorized** — `{"detail": "Authentication credentials were not provided."}`

---

## POST /api/auth/logout/

Requires the access token in the header and the refresh token in the body:

```json
{"refresh": "<refresh token>"}
```

**205 Reset Content** on success. The refresh token is blacklisted, so a later
refresh with it returns 401 `{"detail": "Token is blacklisted"}`.

---

## Notes for the frontend

**Routing by role.** The role is in the login and registration response under
`user.role`, and it is also a claim inside the access token. Use the response
field — it is simpler and does not need the token to be decoded.

```js
const { user, access, refresh } = await login(email, password);
navigate(user.role === "partner" ? "/partner" : "/");
```

**Where to keep the tokens.** For the MVP, `localStorage` is enough. Send the
access token on every request:

```js
fetch("/api/auth/me/", { headers: { Authorization: `Bearer ${access}` } });
```

**On a 401 for a protected request**, call `/api/auth/refresh/` once with the
stored refresh token, save the new pair and retry. If the refresh also returns
401, clear the storage and send the user back to the login page.

**CORS** is open for `http://localhost:5173` and `http://127.0.0.1:5173` (the
Vite dev server). If React runs on another port, add it to `CORS_ALLOWED_ORIGINS`
in `backend/.env`.
