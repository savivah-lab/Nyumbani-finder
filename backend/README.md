# Nyumbani Finder - Backend (FastAPI)
Powered by Savivah Technologies Limited

## Run locally
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
Interactive API docs: http://localhost:8000/docs

## Tests
```bash
python -m pytest -q
```

## Create an admin
```bash
python -m scripts.create_admin 0712345678 "Your Name"
```

## M-Pesa
With no Daraja credentials in `.env` the app runs in **mock mode**: STK pushes are
simulated and you complete them with `POST /api/payments/mock/{payment_id}/complete`.
Add `MPESA_CONSUMER_KEY / SECRET / PASSKEY` and a public `MPESA_CALLBACK_BASE_URL`
to go live (the mock endpoint then switches itself off).

## Key rules enforced in code
- `contact_phone` is only returned to the owner, an admin, or a tenant with a successful unlock payment (`app/services/listings.py`). Everyone else gets `07** *** ***`.
- Listings stay `pending` (invisible) until the listing fee payment succeeds; a photo is required first.
- Payments are idempotent, callbacks are secret-guarded, and underpayments are rejected.
- 3 tenant flags hide a listing for admin review; listings auto-expire after 30 days.
