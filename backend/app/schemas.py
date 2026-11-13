from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import FlagReason, ListingStatus, PaymentStatus, PaymentType, Role
from .utils import normalize_phone


class PhoneMixin(BaseModel):
    @staticmethod
    def _clean(v: str) -> str:
        return normalize_phone(v)


# ---------- Auth ----------
class RegisterIn(BaseModel):
    phone_number: str
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=72)
    role: Role = Role.tenant

    @field_validator("phone_number")
    @classmethod
    def phone(cls, v): return normalize_phone(v)

    @field_validator("role")
    @classmethod
    def no_admin(cls, v):
        if v == Role.admin:
            raise ValueError("Cannot self-register as admin")
        return v


class LoginIn(BaseModel):
    phone_number: str
    password: str

    @field_validator("phone_number")
    @classmethod
    def phone(cls, v): return normalize_phone(v)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    phone_number: str
    full_name: str
    role: Role


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Listings ----------
class ListingCreate(BaseModel):
    title: str = Field(min_length=5, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    house_type: str = Field(min_length=2, max_length=30)   # bedsitter, 1br, 2br, ...
    rent_amount: float = Field(gt=0, le=10_000_000)
    area_name: str | None = Field(default=None, max_length=120)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    contact_phone: str

    @field_validator("contact_phone")
    @classmethod
    def phone(cls, v): return normalize_phone(v)


class ListingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=5, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    rent_amount: float | None = Field(default=None, gt=0, le=10_000_000)
    area_name: str | None = None
    contact_phone: str | None = None
    status: ListingStatus | None = None   # landlord may only set 'rented' or 'removed'

    @field_validator("contact_phone")
    @classmethod
    def phone(cls, v): return normalize_phone(v) if v else v


class ListingOut(BaseModel):
    id: int
    title: str
    description: str | None
    house_type: str
    rent_amount: float
    area_name: str | None
    latitude: float
    longitude: float
    status: ListingStatus
    is_featured: bool
    expires_at: datetime | None
    created_at: datetime
    photos: list[str]
    distance_km: float | None = None
    contact_unlocked: bool
    # The real number if unlocked/owner/admin, otherwise a masked placeholder like 07** *** ***
    contact_phone: str


class ListingPage(BaseModel):
    items: list[ListingOut]
    total: int
    limit: int
    offset: int


class FlagIn(BaseModel):
    reason: FlagReason
    notes: str | None = Field(default=None, max_length=500)


# ---------- Payments ----------
class PayIn(BaseModel):
    phone_number: str | None = None   # M-Pesa number to charge; defaults to the user's own

    @field_validator("phone_number")
    @classmethod
    def phone(cls, v): return normalize_phone(v) if v else v


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: PaymentType
    listing_id: int
    amount: float
    status: PaymentStatus
    mpesa_receipt: str | None
    failure_reason: str | None
    created_at: datetime


class InitiatePaymentOut(BaseModel):
    payment: PaymentOut | None = None
    already_unlocked: bool = False
    contact_phone: str | None = None
    message: str
