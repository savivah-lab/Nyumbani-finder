from .conftest import PNG, make_live_listing, register


def test_phone_normalisation_and_duplicate(client):
    register(client, "+254 712 345 678", "tenant")
    r = client.post("/api/auth/login", json={"phone_number": "0712345678", "password": "password123"})
    assert r.status_code == 200 and r.json()["user"]["phone_number"] == "254712345678"
    r = client.post("/api/auth/register", json={"phone_number": "0712345678", "full_name": "Dup", "password": "password123"})
    assert r.status_code == 409


def test_cannot_register_as_admin_or_bad_phone(client):
    r = client.post("/api/auth/register", json={"phone_number": "0712345678", "full_name": "X Y", "password": "password123", "role": "admin"})
    assert r.status_code == 422
    r = client.post("/api/auth/register", json={"phone_number": "12345", "full_name": "X Y", "password": "password123"})
    assert r.status_code == 422


def test_draft_listing_invisible_until_paid(client, landlord):
    r = client.post("/api/listings", headers=landlord, json={
        "title": "Draft house", "house_type": "bedsitter", "rent_amount": 5000,
        "latitude": -1.3, "longitude": 36.8, "contact_phone": "0700000000"})
    lid = r.json()["id"]
    assert client.get("/api/listings").json()["total"] == 0
    assert client.get(f"/api/listings/{lid}").status_code == 404
    # photo required before paying
    assert client.post(f"/api/payments/listing-fee/{lid}", headers=landlord, json={}).status_code == 400


def test_tenant_cannot_create_listing(client, tenant):
    r = client.post("/api/listings", headers=tenant, json={
        "title": "Sneaky", "house_type": "1br", "rent_amount": 1000,
        "latitude": 0, "longitude": 0, "contact_phone": "0700000000"})
    assert r.status_code == 403


def test_phone_masked_until_unlocked_then_revealed(client, landlord, tenant, tenant2):
    lid = make_live_listing(client, landlord, phone="0799999999")

    # anonymous, tenant: masked everywhere
    for headers in ({}, tenant):
        d = client.get(f"/api/listings/{lid}", headers=headers).json()
        assert d["contact_unlocked"] is False and "799999999" not in d["contact_phone"]
        s = client.get("/api/listings", headers=headers).json()["items"][0]
        assert "799999999" not in s["contact_phone"]

    # owner always sees it
    assert client.get(f"/api/listings/{lid}", headers=landlord).json()["contact_phone"] == "254799999999"

    # unlock: pending payment does NOT reveal
    res = client.post(f"/api/payments/unlock/{lid}", headers=tenant, json={}).json()
    pid = res["payment"]["id"]
    assert client.get(f"/api/listings/{lid}", headers=tenant).json()["contact_unlocked"] is False

    # cancelled PIN -> still hidden
    client.post(f"/api/payments/mock/{pid}/complete?success=false", headers=tenant)
    assert client.get(f"/api/listings/{lid}", headers=tenant).json()["contact_unlocked"] is False

    # pay properly
    pid2 = client.post(f"/api/payments/unlock/{lid}", headers=tenant, json={}).json()["payment"]["id"]
    assert pid2 != pid
    client.post(f"/api/payments/mock/{pid2}/complete", headers=tenant)
    d = client.get(f"/api/listings/{lid}", headers=tenant).json()
    assert d["contact_unlocked"] is True and d["contact_phone"] == "254799999999"

    # unlocking again is free
    again = client.post(f"/api/payments/unlock/{lid}", headers=tenant, json={}).json()
    assert again["already_unlocked"] is True

    # the OTHER tenant is still locked out
    assert client.get(f"/api/listings/{lid}", headers=tenant2).json()["contact_unlocked"] is False


def test_no_double_charge_while_payment_pending(client, landlord, tenant):
    lid = make_live_listing(client, landlord)
    a = client.post(f"/api/payments/unlock/{lid}", headers=tenant, json={}).json()["payment"]["id"]
    b = client.post(f"/api/payments/unlock/{lid}", headers=tenant, json={}).json()["payment"]["id"]
    assert a == b


def test_mpesa_callback_secret_and_underpayment(client, landlord, tenant):
    lid = make_live_listing(client, landlord)
    pay = client.post(f"/api/payments/unlock/{lid}", headers=tenant, json={}).json()["payment"]
    from app.database import SessionLocal
    from app.models import Payment
    with SessionLocal() as db:
        ckid = db.get(Payment, pay["id"]).checkout_request_id

    def body(amount):
        return {"Body": {"stkCallback": {"CheckoutRequestID": ckid, "ResultCode": 0, "ResultDesc": "ok",
                "CallbackMetadata": {"Item": [{"Name": "Amount", "Value": amount}, {"Name": "MpesaReceiptNumber", "Value": "QWE123"}]}}}}

    assert client.post("/api/payments/mpesa/callback?secret=wrong", json=body(30)).status_code == 403
    client.post("/api/payments/mpesa/callback?secret=dev-callback-secret", json=body(1))   # underpaid
    assert client.get(f"/api/payments/{pay['id']}", headers=tenant).json()["status"] == "failed"
    assert client.get(f"/api/listings/{lid}", headers=tenant).json()["contact_unlocked"] is False

    pay2 = client.post(f"/api/payments/unlock/{lid}", headers=tenant, json={}).json()["payment"]
    with SessionLocal() as db:
        ckid = db.get(Payment, pay2["id"]).checkout_request_id
    cb = body(30)
    client.post("/api/payments/mpesa/callback?secret=dev-callback-secret", json=cb)
    client.post("/api/payments/mpesa/callback?secret=dev-callback-secret", json=cb)  # retry is harmless
    assert client.get(f"/api/listings/{lid}", headers=tenant).json()["contact_unlocked"] is True


def test_radius_search_and_filters(client, landlord):
    near = make_live_listing(client, landlord, lat=-1.2921, lng=36.8219, rent=10000)           # Nairobi CBD
    make_live_listing(client, landlord, lat=-1.2864, lng=36.8172, rent=30000)                  # ~0.7km away, pricey
    make_live_listing(client, landlord, lat=-4.0435, lng=39.6682, rent=8000)                   # Mombasa
    r = client.get("/api/listings", params={"lat": -1.2921, "lng": 36.8219, "radius_km": 5}).json()
    assert r["total"] == 2 and r["items"][0]["id"] == near and r["items"][0]["distance_km"] == 0
    r = client.get("/api/listings", params={"lat": -1.2921, "lng": 36.8219, "radius_km": 5, "max_price": 12000}).json()
    assert r["total"] == 1
    assert client.get("/api/listings", params={"lat": -1.29}).status_code == 422
    assert client.get("/api/listings").json()["total"] == 3


def test_flags_hide_listing_after_threshold(client, landlord):
    lid = make_live_listing(client, landlord)
    for i in range(3):
        t = register(client, f"07440000{i:02d}", "tenant")
        r = client.post(f"/api/listings/{lid}/flag", headers=t, json={"reason": "fake"})
        assert r.status_code == 201
        if i == 0:
            assert client.post(f"/api/listings/{lid}/flag", headers=t, json={"reason": "fake"}).status_code == 409
    assert client.get("/api/listings").json()["total"] == 0


def test_landlord_marks_rented_and_cant_edit_others(client, landlord, tenant):
    lid = make_live_listing(client, landlord)
    assert client.patch(f"/api/listings/{lid}", headers=tenant, json={"title": "Hacked title"}).status_code == 403
    assert client.patch(f"/api/listings/{lid}", headers=landlord, json={"status": "active"}).status_code == 400
    assert client.patch(f"/api/listings/{lid}", headers=landlord, json={"status": "rented"}).status_code == 200
    assert client.get("/api/listings").json()["total"] == 0


def test_upload_rejects_non_images(client, landlord):
    r = client.post("/api/listings", headers=landlord, json={
        "title": "Upload test", "house_type": "1br", "rent_amount": 1000,
        "latitude": 0, "longitude": 0, "contact_phone": "0700000000"})
    lid = r.json()["id"]
    bad = client.post(f"/api/listings/{lid}/photos", headers=landlord, files=[("files", ("x.png", b"<?php evil ?>", "image/png"))])
    assert bad.status_code == 415


def test_expiry_job(client, landlord):
    lid = make_live_listing(client, landlord)
    from datetime import timedelta
    from app.database import SessionLocal
    from app.models import Listing, utcnow
    from app.services.payments import expire_listings
    with SessionLocal() as db:
        db.get(Listing, lid).expires_at = utcnow() - timedelta(days=1)
        db.commit()
        assert expire_listings(db) == 1
    assert client.get("/api/listings").json()["total"] == 0
    assert client.get(f"/api/listings/{lid}", headers=landlord).json()["status"] == "expired"


def test_admin_only_endpoints(client, landlord, tenant):
    from app.database import SessionLocal
    from app.models import Role, User
    from app.security import create_access_token, hash_password
    lid = make_live_listing(client, landlord)
    assert client.get("/api/admin/stats", headers=tenant).status_code == 403
    assert client.get("/api/admin/stats").status_code == 401
    with SessionLocal() as db:
        u = User(phone_number="254700000001", full_name="Admin", password_hash=hash_password("password123"), role=Role.admin)
        db.add(u); db.commit()
        admin = {"Authorization": f"Bearer {create_access_token(u.id, 'admin')}"}
    s = client.get("/api/admin/stats", headers=admin).json()
    assert s["revenue_kes"]["listing_fees"] == 250 and s["listings_by_status"]["active"] == 1
    assert client.post(f"/api/admin/listings/{lid}/status?status=removed", headers=admin).status_code == 200
    assert client.get("/api/listings").json()["total"] == 0


def test_database_url_normalised_for_render():
    from app.config import Settings
    assert Settings(database_url="postgres://u:p@h/db").database_url == "postgresql+psycopg2://u:p@h/db"
    assert Settings(database_url="postgresql://u:p@h/db").database_url == "postgresql+psycopg2://u:p@h/db"
    assert Settings(database_url="sqlite:///x.db").database_url == "sqlite:///x.db"


def test_mock_payments_locked_in_production_unless_allowed():
    from app.config import Settings
    base = dict(mpesa_consumer_key="", mpesa_consumer_secret="", mpesa_passkey="")
    assert Settings(app_env="production", **base).mock_enabled is False
    assert Settings(app_env="production", **base).payment_mode == "unconfigured"
    assert Settings(app_env="production", allow_mock_payments=True, **base).payment_mode == "mock"
    assert Settings(app_env="development", **base).payment_mode == "mock"
    live = Settings(app_env="production", mpesa_consumer_key="k", mpesa_consumer_secret="s", mpesa_passkey="p")
    assert live.mock_enabled is False and live.payment_mode == "sandbox"


def test_admin_bootstrap_creates_and_promotes_without_overwriting_password(client, tenant):
    from app import main
    from app.database import SessionLocal
    from app.models import Role, User
    from app.security import verify_password
    main.settings.admin_phone, main.settings.admin_password = "0788888888", "StrongPass123"
    try:
        main.bootstrap_admin()
        r = client.post("/api/auth/login", json={"phone_number": "0788888888", "password": "StrongPass123"})
        assert r.status_code == 200 and r.json()["user"]["role"] == "admin"
        # promoting an existing tenant keeps their own password
        main.settings.admin_phone = "0722222222"
        main.bootstrap_admin()
        with SessionLocal() as db:
            u = db.query(User).filter_by(phone_number="254722222222").one()
            assert u.role == Role.admin and verify_password("password123", u.password_hash)
    finally:
        main.settings.admin_phone = main.settings.admin_password = ""
