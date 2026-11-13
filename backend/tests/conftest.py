import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ.update({
    "APP_ENV": "test",
    "DATABASE_URL": f"sqlite:///{_tmp}/test.db",
    "UPLOAD_DIR": f"{_tmp}/uploads",
    "MPESA_CONSUMER_KEY": "", "MPESA_CONSUMER_SECRET": "", "MPESA_PASSKEY": "",
})

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with TestClient(app) as c:
        yield c


def register(client, phone, role, name="Test User"):
    r = client.post("/api/auth/register", json={"phone_number": phone, "full_name": name, "password": "password123", "role": role})
    assert r.status_code == 201, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def landlord(client): return register(client, "0711111111", "landlord", "Landlord")
@pytest.fixture()
def tenant(client): return register(client, "0722222222", "tenant", "Tenant")
@pytest.fixture()
def tenant2(client): return register(client, "0733333333", "tenant", "Tenant Two")


def make_live_listing(client, landlord, lat=-1.2921, lng=36.8219, rent=15000, phone="0799999999"):
    r = client.post("/api/listings", headers=landlord, json={
        "title": "Nice 1BR in Kilimani", "house_type": "1br", "rent_amount": rent, "area_name": "Kilimani",
        "latitude": lat, "longitude": lng, "contact_phone": phone})
    assert r.status_code == 201, r.text
    lid = r.json()["id"]
    r = client.post(f"/api/listings/{lid}/photos", headers=landlord, files=[("files", ("a.png", PNG, "image/png"))])
    assert r.status_code == 201, r.text
    pay = client.post(f"/api/payments/listing-fee/{lid}", headers=landlord, json={}).json()["payment"]
    r = client.post(f"/api/payments/mock/{pay['id']}/complete", headers=landlord)
    assert r.json()["status"] == "success"
    return lid
