"""Run against a local server with seeded demo points: python scripts/api_smoke.py URL."""
import json
import sys
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080").rstrip("/")
def call(path, method="GET", body=None, token=None, expected=200):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(BASE + "/api" + path, data=json.dumps(body).encode() if body is not None else None, headers=headers, method=method)
    try:
        response = urlopen(request, timeout=15)
    except HTTPError as error:
        response = error
    with response:
        data = response.read()
        assert response.status == expected, (path, response.status, data)
        return json.loads(data) if data else None

call("/health/")
call("/storage-points/", expected=401)
email = "smoke-" + uuid.uuid4().hex + "@example.com"
user = {"full_name": "Smoke User", "email": email, "password": "SmokeComplex2026!", "role": "traveler"}
session = call("/auth/register/", "POST", user, expected=201)
call("/auth/register/", "POST", user, expected=400)
call("/auth/login/", "POST", {"email": email, "password": "wrong"}, expected=401)
session = call("/auth/login/", "POST", {"email": email, "password": user["password"]})
token = session["access"]
assert call("/auth/me/", token=token)["email"] == email
assert len(call("/districts/", token=token)) == 8
points = call("/storage-points/?district=medeu", token=token)
assert points and all(p["district_code"] == "medeu" for p in points)
assert "price_per_bag_per_hour" in points[0]
assert "address" in call(f"/storage-points/{points[0]['id']}/", token=token)
call("/storage-points/99999999/", token=token, expected=404)
call("/storage-points/?district=unknown", token=token, expected=400)
new = call("/auth/refresh/", "POST", {"refresh": session["refresh"]})
call("/auth/refresh/", "POST", {"refresh": session["refresh"]}, expected=401)
call("/auth/logout/", "POST", {"refresh": new["refresh"]}, token=new["access"], expected=205)
call("/auth/refresh/", "POST", {"refresh": new["refresh"]}, expected=401)
print("API smoke: PASS (register, duplicate, login, auth, districts, filter, detail, 404, refresh rotation, logout)")
