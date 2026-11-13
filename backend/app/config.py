from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "sqlite:///./nyumbani.db"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    listing_fee: int = 250
    unlock_fee: int = 30
    listing_expiry_days: int = 30
    flags_before_review: int = 3

    mpesa_env: str = "sandbox"
    mpesa_consumer_key: str = ""
    mpesa_consumer_secret: str = ""
    mpesa_shortcode: str = "174379"
    mpesa_passkey: str = ""
    mpesa_callback_base_url: str = ""
    mpesa_callback_secret: str = "dev-callback-secret"

    upload_dir: str = "./uploads"
    cors_origins: str = "http://localhost:5173"

    # Persistent photo storage (required on Render: its disk is wiped on every deploy)
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    @field_validator("database_url")
    @classmethod
    def _fix_db_url(cls, v: str) -> str:
        # Render/Heroku hand out postgres:// or postgresql://; SQLAlchemy needs a driver suffix.
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            v = "postgresql+psycopg2://" + v[len("postgresql://"):]
        return v

    @property
    def cloudinary_enabled(self) -> bool:
        return bool(self.cloudinary_cloud_name and self.cloudinary_api_key and self.cloudinary_api_secret)

    # Production safety: mock payments (free "simulate PIN" endpoint) must be explicitly allowed.
    allow_mock_payments: bool = False

    # Optional first-admin bootstrap (Render's free tier has no shell to run a script)
    admin_phone: str = ""
    admin_password: str = ""
    admin_name: str = "Admin"

    @property
    def mock_enabled(self) -> bool:
        return self.mpesa_mock and (self.app_env != "production" or self.allow_mock_payments)

    @property
    def payment_mode(self) -> str:
        if self.mock_enabled: return "mock"
        return "unconfigured" if self.mpesa_mock else self.mpesa_env

    @property
    def mpesa_mock(self) -> bool:
        """No credentials configured -> mock mode, no real money moves."""
        return not (self.mpesa_consumer_key and self.mpesa_consumer_secret and self.mpesa_passkey)


@lru_cache
def get_settings() -> Settings:
    return Settings()
