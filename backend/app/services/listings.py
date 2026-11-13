"""Listing serialisation. THE one place where phone-number masking is decided."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Listing, Role, Unlock, User
from ..schemas import ListingOut
from ..utils import mask_phone


def unlocked_listing_ids(db: Session, viewer: User | None, listing_ids: list[int]) -> set[int]:
    if not viewer or not listing_ids:
        return set()
    return set(db.scalars(select(Unlock.listing_id).where(Unlock.tenant_id == viewer.id, Unlock.listing_id.in_(listing_ids))))


def serialize(listing: Listing, viewer: User | None, unlocked_ids: set[int], distance_km: float | None = None) -> ListingOut:
    is_owner = viewer is not None and viewer.id == listing.landlord_id
    is_admin = viewer is not None and viewer.role == Role.admin
    can_see = is_owner or is_admin or listing.id in unlocked_ids
    return ListingOut(
        id=listing.id, title=listing.title, description=listing.description, house_type=listing.house_type,
        rent_amount=float(listing.rent_amount), area_name=listing.area_name,
        latitude=listing.latitude, longitude=listing.longitude, status=listing.status,
        is_featured=listing.is_featured, expires_at=listing.expires_at, created_at=listing.created_at,
        photos=[p.url for p in listing.photos],
        distance_km=round(distance_km, 2) if distance_km is not None else None,
        contact_unlocked=can_see,
        contact_phone=listing.contact_phone if can_see else mask_phone(listing.contact_phone),
    )
