import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from sqlalchemy import select

from .database import Base, SessionLocal, engine
from .models import Role, User
from .security import hash_password
from .utils import normalize_phone
from .routers import admin, auth, listings, payments
from .services.payments import expire_listings

settings = get_settings()


async def _expiry_loop():
    while True:
        with SessionLocal() as db:
            expire_listings(db)
        await asyncio.sleep(3600)


def bootstrap_admin() -> None:
    """Create (or promote) the admin from ADMIN_PHONE / ADMIN_PASSWORD env vars. Never overwrites a password."""
    if not (settings.admin_phone and settings.admin_password):
        return
    phone = normalize_phone(settings.admin_phone)
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.phone_number == phone))
        if user is None:
            db.add(User(phone_number=phone, full_name=settings.admin_name, role=Role.admin,
                        password_hash=hash_password(settings.admin_password)))
        elif user.role != Role.admin:
            user.role = Role.admin
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)   # use Alembic migrations once the schema stabilises
    bootstrap_admin()
    if settings.mpesa_mock and settings.app_env == "production" and settings.allow_mock_payments:
        print("WARNING: mock payments are ENABLED in production. Anyone can unlock numbers for free. "
              "Set ALLOW_MOCK_PAYMENTS=false and add M-Pesa credentials before launch.")
    task = asyncio.create_task(_expiry_loop()) if settings.app_env != "test" else None
    yield
    if task:
        task.cancel()


app = FastAPI(title="Nyumbani Finder API", version="0.1.0",
              description="Powered by Savivah Technologies Limited", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

for r in (auth.router, listings.router, payments.router, admin.router):
    app.include_router(r)


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok", "mpesa_mode": settings.payment_mode}


@app.get("/api/config", tags=["meta"])
def public_config():
    """Non-secret settings the frontend needs to display fees and payment mode."""
    return {
        "listing_fee": settings.listing_fee,
        "unlock_fee": settings.unlock_fee,
        "listing_expiry_days": settings.listing_expiry_days,
        "mpesa_mode": settings.payment_mode,
    }
