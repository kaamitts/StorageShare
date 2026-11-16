"""Sprint 3 end-to-end check (US-07, US-08, US-09) over real HTTP.

Run against the Docker stack:  python scripts/sprint3_smoke.py http://localhost:8080
Creates fresh users each run, so it can be repeated.
"""
import json
import sys
import uuid
from datetime import date, datetime, time, timedelta, timezone
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080").rstrip("/")
ALMATY = timezone(timedelta(hours=5))
PASSWORD = "SmokeComplex2026!"
step = 0


def call(path, method="GET", body=None, token=None, expected=200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body).encode() if body is not None else None
    request = Request(BASE + "/api" + path, data=data, headers=headers, method=method)
    try:
        response = urlopen(request, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read()
        payload = json.loads(raw) if raw else None
        assert response.status == expected, (method, path, response.status, payload)
        return payload


def ok(message):
    global step
    step += 1
    print(f"  [{step:02}] OK  {message}")


def register(role, name):
    email = f"s3-{role}-{uuid.uuid4().hex[:10]}@example.com"
    call("/auth/register/", "POST", {
        "email": email, "password": PASSWORD, "full_name": name, "role": role,
    }, expected=201)
    return call("/auth/login/", "POST", {"email": email, "password": PASSWORD})["access"]


print(f"Sprint 3 smoke test against {BASE}")
partner = register("partner", "Owner Partner")
other_partner = register("partner", "Other Partner")
traveler = register("traveler", "Smoke Traveler")
ok("registered two partners and a traveler")

# US-07 -----------------------------------------------------------------
print("US-07 Partner adds a storage point")
point_body = {
    "name": f"Smoke point {uuid.uuid4().hex[:6]}", "address": "Abay ave 1",
    "district": "alatau", "price_per_bag_per_hour": "250.00", "capacity_bags": 5,
    "opens_at": "08:00", "closes_at": "22:00", "security_notes": "CCTV",
}
for field, bad in (
    ("price_per_bag_per_hour", {"price_per_bag_per_hour": ""}),
    ("price_per_bag_per_hour", {"price_per_bag_per_hour": "-5"}),
    ("capacity_bags", {"capacity_bags": 0}),
    ("district", {"district": "downtown"}),
    ("closes_at", {"opens_at": "22:00", "closes_at": "08:00"}),
):
    errors = call("/storage-points/", "POST", {**point_body, **bad}, partner, expected=400)
    assert field in errors, errors
    ok(f"400 with field '{field}' for {bad}")
call("/storage-points/", "POST", point_body, traveler, expected=403)
ok("traveler gets 403")
point = call("/storage-points/", "POST", {**point_body, "partner": 999999}, partner, expected=201)
ok(f"partner created point #{point['id']} (partner from token, not body)")
listed = call("/storage-points/?district=alatau", token=traveler)
assert point["id"] in [p["id"] for p in listed]
ok("point appears in GET /storage-points/?district=alatau")

# US-08 -----------------------------------------------------------------
print("US-08 Partner sees bookings")
assert call("/partner/bookings/", token=partner) == []
ok("new partner has no bookings yet (empty list)")
call("/partner/bookings/", token=traveler, expected=403)
ok("traveler gets 403")

day = date.today() + timedelta(days=3)
start = datetime.combine(day, time(10), ALMATY)
booking = call("/bookings/", "POST", {
    "storage_point": point["id"], "drop_off_at": start.isoformat(),
    "pick_up_at": (start + timedelta(hours=2)).isoformat(), "bags_count": 2,
}, traveler, expected=201)
assert booking["status"] == "awaiting_payment"
assert call("/partner/bookings/", token=partner) == []
ok("unpaid booking is not shown to the partner")

call(f"/bookings/{booking['id']}/pay/", "POST", token=traveler)
items = call("/partner/bookings/", token=partner)
assert [b["id"] for b in items] == [booking["id"]], items
assert items[0]["bags_count"] == 2 and items[0]["storage_point_name"] == point_body["name"]
ok("after payment the partner sees it with date, time and bags")
assert call("/partner/bookings/", token=other_partner) == []
ok("another partner does not see it")

# US-09 -----------------------------------------------------------------
print("US-09 Check-in and check-out via QR link")
history = call("/bookings/history/", token=traveler)
qr = next(b for b in history if b["id"] == booking["id"])["qr"]
token = qr["token"]
assert qr["url"].endswith("/partner/check-in/" + token) and str(booking["id"]) != token
ok(f"traveler's history has QR link {qr['url'][:60]}...")

page = call(f"/bookings/by-token/{token}/", token=partner)
assert page["can_check_in"] and not page["can_check_out"]
ok("owner opens the check-in page")
call(f"/bookings/by-token/{token}/", token=other_partner, expected=403)
call(f"/bookings/by-token/{token}/check-in/", "POST", token=other_partner, expected=403)
ok("another partner gets 403 and cannot check in")
call(f"/bookings/by-token/{token}/check-in/", "POST", token=traveler, expected=403)
ok("traveler gets 403")
call("/bookings/by-token/not-a-real-token/check-in/", "POST", token=partner, expected=404)
ok("unknown token gets 404")
err = call(f"/bookings/by-token/{token}/check-out/", "POST", token=partner, expected=409)
ok(f"check-out before check-in -> 409 '{err['detail']}'")

done = call(f"/bookings/by-token/{token}/check-in/", "POST", token=partner)
assert done["status"] == "checked_in" and done["checked_in_at"]
ok(f"check-in -> checked_in at {done['checked_in_at']}")
err = call(f"/bookings/by-token/{token}/check-in/", "POST", token=partner, expected=409)
ok(f"second check-in -> 409 '{err['detail']}'")

done = call(f"/bookings/by-token/{token}/check-out/", "POST", token=partner)
assert done["status"] == "completed" and done["checked_out_at"]
ok(f"check-out -> completed at {done['checked_out_at']}")
item = next(b for b in call("/bookings/history/", token=traveler) if b["id"] == booking["id"])
assert item["status"] == "completed" and item["qr"] is None
ok("QR is gone from the traveler's history")
call(f"/bookings/by-token/{token}/check-out/", "POST", token=partner, expected=409)
ok("second check-out -> 409")

print(f"Sprint 3 smoke: PASS ({step} checks)")
