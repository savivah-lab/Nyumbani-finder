import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey, Index, Integer, Numeric, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Role(str, enum.Enum):
    tenant = "tenant"
    landlord = "landlord"
    admin = "admin"


class ListingStatus(str, enum.Enum):
    pending = "pending"          # created, listing fee not yet paid
    active = "active"            # paid and visible
    under_review = "under_review"  # hidden after too many flags
    expired = "expired"
    rented = "rented"
    removed = "removed"


class PaymentType(str, enum.Enum):
    listing_fee = "listing_fee"
    unlock_fee = "unlock_fee"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    success = "success"
    failed = "failed"


class FlagReason(str, enum.Enum):
    already_rented = "already_rented"
    wrong_location = "wrong_location"
    fake = "fake"
    unreachable_number = "unreachable_number"
    other = "other"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    phone_number: Mapped[str] = mapped_column(String(15), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.tenant)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    listings: Mapped[list["Listing"]] = relationship(back_populates="landlord")


class Listing(Base):
    __tablename__ = "listings"
    __table_args__ = (Index("ix_listings_geo", "latitude", "longitude"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    landlord_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    house_type: Mapped[str] = mapped_column(String(30), index=True)
    rent_amount: Mapped[float] = mapped_column(Numeric(12, 2))
    area_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    contact_phone: Mapped[str] = mapped_column(String(15))
    status: Mapped[ListingStatus] = mapped_column(Enum(ListingStatus), default=ListingStatus.pending, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    landlord: Mapped[User] = relationship(back_populates="listings")
    photos: Mapped[list["ListingPhoto"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan", order_by="ListingPhoto.sort_order"
    )


class ListingPhoto(Base):
    __tablename__ = "listing_photos"
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    listing: Mapped[Listing] = relationship(back_populates="photos")


class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    type: Mapped[PaymentType] = mapped_column(Enum(PaymentType))
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    phone_number: Mapped[str] = mapped_column(String(15))
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.pending, index=True)
    checkout_request_id: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True)
    mpesa_receipt: Mapped[str | None] = mapped_column(String(50), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Unlock(Base):
    """A tenant paid to see one listing's phone number. One row per (tenant, listing)."""
    __tablename__ = "unlocks"
    __table_args__ = (UniqueConstraint("tenant_id", "listing_id", name="uq_unlock_tenant_listing"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ListingFlag(Base):
    __tablename__ = "listing_flags"
    __table_args__ = (UniqueConstraint("tenant_id", "listing_id", name="uq_flag_tenant_listing"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[FlagReason] = mapped_column(Enum(FlagReason))
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
