# Nyumbani Finder
**by Savivah Netcore Technologies Limited**

Map-based marketplace for vacant rental houses. Landlords pay to post; tenants browse free and pay a small fee to unlock the landlord's phone number.

```
backend/    FastAPI + SQLAlchemy API (auth, listings, M-Pesa payments, admin)
frontend/   React + Vite website (dark/gold theme, Leaflet maps)
render.yaml Render Blueprint: deploys API + website + Postgres
```

## Run locally
```bash
# API  (http://localhost:8000/docs)
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
uvicorn app.main:app --reload

# Website (http://localhost:5173)
cd frontend && cp .env.example .env && npm install && npm run dev
```
With no M-Pesa keys the app runs in **test mode**: the payment pop-up shows "Enter PIN (success)" buttons and no real money moves.

Tests: `cd backend && python -m pytest -q`

## Deploy on Render
1. Push this repo to GitHub.
2. Render dashboard -> **New -> Blueprint** -> choose the repo. Render creates the database, API and website from `render.yaml` and asks for the blank values.
3. Fill in:
   - `CLOUDINARY_*` - free account at cloudinary.com (photos need permanent storage).
   - `ADMIN_PHONE` / `ADMIN_PASSWORD` - your admin login.
   - Leave `CORS_ORIGINS`, `MPESA_CALLBACK_BASE_URL`, `VITE_API_URL` as placeholders for now.
4. After the first deploy note the two URLs Render gave you, then set:
   - API service: `CORS_ORIGINS` = website URL, `MPESA_CALLBACK_BASE_URL` = API URL
   - Website: `VITE_API_URL` = API URL, then **Manual Deploy -> Clear cache & deploy** (the value is baked in at build time).
5. Open the website, log in with the admin phone, and try the full flow.

### Before real users
- [ ] Get Daraja credentials, set `MPESA_CONSUMER_KEY/SECRET/PASSKEY`, `MPESA_SHORTCODE`, `MPESA_ENV=production`.
- [ ] Set `ALLOW_MOCK_PAYMENTS=false` (otherwise anyone can unlock numbers for free).
- [ ] Upgrade the database off the free plan (free databases expire) and the API off the free plan (it sleeps when idle).
- [ ] Map tiles/search use free OpenStreetMap services, fine for launch; switch to a paid provider (`VITE_MAP_TILES_URL`) as traffic grows.
