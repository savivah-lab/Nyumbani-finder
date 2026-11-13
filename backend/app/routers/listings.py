from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user, get_optional_user, require_role
from ..models import FlagReason, Listing, ListingFlag, ListingPhoto, ListingStatus, Role, User, utcnow
from ..schemas import FlagIn, ListingCreate, ListingOut, ListingPage, ListingUpdate
from ..services.listings import serialize, unlocked_listing_ids
from ..services.storage import save_image
from ..utils import bounding_box, haversine_km

settings = get_settings()
router = APIRouter(prefix="/api/listings", tags=["listings"])
MAX_PHOTOS = 8


def _get_owned(db: Session, listing_id: int, user: User) -> Listing:
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing.landlord_id != user.id and user.role != Role.admin:
        raise HTTPException(403, "This is not your listing")
    return listing


@router.get("", response_model=ListingPage)
def search(
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    radius_km: float = Query(5, gt=0, le=50),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    house_type: str | None = None,
    area: str | None = Query(None, max_length=120),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    viewer: User | None = Depends(get_optional_user),
):
    """Public, free search. Only live listings appear; phone numbers are masked unless unlocked."""
    if (lat is None) != (lng is None):
        raise HTTPException(422, "Provide both lat and lng, or neither")

    conds = [Listing.status == ListingStatus.active, or_(Listing.expires_at.is_(None), Listing.expires_at > utcnow())]
    if min_price is not None: conds.append(Listing.rent_amount >= min_price)
    if max_price is not None: conds.append(Listing.rent_amount <= max_price)
    if house_type: conds.append(func.lower(Listing.house_type) == house_type.lower())
    if area: conds.append(Listing.area_name.ilike(f"%{area}%"))

    base = select(Listing).options(selectinload(Listing.photos))
    if lat is not None:
        s, n, w, e = bounding_box(lat, lng, radius_km)
        conds += [Listing.latitude.between(s, n), Listing.longitude.between(w, e)]
        rows = db.scalars(base.where(and_(*conds))).all()
        scored = [(l, haversine_km(lat, lng, l.latitude, l.longitude)) for l in rows]
        scored = [(l, d) for l, d in scored if d <= radius_km]
        scored.sort(key=lambda x: (not x[0].is_featured, x[1]))
        total = len(scored)
        page = scored[offset: offset + limit]
    else:
        total = db.scalar(select(func.count()).select_from(Listing).where(and_(*conds)))
        rows = db.scalars(base.where(and_(*conds)).order_by(Listing.is_featured.desc(), Listing.created_at.desc())
                          .limit(limit).offset(offset)).all()
        page = [(l, None) for l in rows]

    unlocked = unlocked_listing_ids(db, viewer, [l.id for l, _ in page])
    return ListingPage(items=[serialize(l, viewer, unlocked, d) for l, d in page], total=total, limit=limit, offset=offset)


@router.get("/mine", response_model=list[ListingOut])
def my_listings(db: Session = Depends(get_db), user: User = Depends(require_role(Role.landlord, Role.admin))):
    rows = db.scalars(select(Listing).options(selectinload(Listing.photos))
                      .where(Listing.landlord_id == user.id).order_by(Listing.created_at.desc())).all()
    return [serialize(l, user, set()) for l in rows]


@router.get("/{listing_id}", response_model=ListingOut)
def get_listing(listing_id: int, db: Session = Depends(get_db), viewer: User | None = Depends(get_optional_user)):
    listing = db.scalar(select(Listing).options(selectinload(Listing.photos)).where(Listing.id == listing_id))
    if not listing:
        raise HTTPException(404, "Listing not found")
    privileged = viewer is not None and (viewer.id == listing.landlord_id or viewer.role == Role.admin)
    if listing.status != ListingStatus.active and not privileged:
        raise HTTPException(404, "Listing not found")
    return serialize(listing, viewer, unlocked_listing_ids(db, viewer, [listing.id]))


@router.post("", response_model=ListingOut, status_code=201)
def create_listing(body: ListingCreate, db: Session = Depends(get_db),
                   user: User = Depends(require_role(Role.landlord, Role.admin))):
    """Creates a draft (status=pending). It goes live only after the listing fee is paid."""
    listing = Listing(landlord_id=user.id, **body.model_dump())
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return serialize(listing, user, set())


@router.patch("/{listing_id}", response_model=ListingOut)
def update_listing(listing_id: int, body: ListingUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    listing = _get_owned(db, listing_id, user)
    data = body.model_dump(exclude_unset=True)
    new_status = data.pop("status", None)
    if new_status is not None:
        if new_status not in (ListingStatus.rented, ListingStatus.removed):
            raise HTTPException(400, "You can only mark a listing as rented or removed. To relist, pay the listing fee again.")
        listing.status = new_status
    for k, v in data.items():
        setattr(listing, k, v)
    db.commit()
    db.refresh(listing)
    return serialize(listing, user, set())


@router.post("/{listing_id}/photos", response_model=ListingOut, status_code=201)
async def upload_photos(listing_id: int, files: list[UploadFile] = File(...), db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    listing = _get_owned(db, listing_id, user)
    if len(listing.photos) + len(files) > MAX_PHOTOS:
        raise HTTPException(400, f"A listing can have at most {MAX_PHOTOS} photos")
    start = len(listing.photos)
    for i, f in enumerate(files):
        listing.photos.append(ListingPhoto(url=await save_image(f), sort_order=start + i))
    db.commit()
    db.refresh(listing)
    return serialize(listing, user, set())


@router.post("/{listing_id}/flag", status_code=201)
def flag_listing(listing_id: int, body: FlagIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Tenants report fake / already-rented / wrong-location listings. Enough flags hides it for review."""
    listing = db.get(Listing, listing_id)
    if not listing or listing.status != ListingStatus.active:
        raise HTTPException(404, "Listing not found")
    if listing.landlord_id == user.id:
        raise HTTPException(400, "You cannot flag your own listing")
    if db.scalar(select(ListingFlag).where(ListingFlag.listing_id == listing_id, ListingFlag.tenant_id == user.id)):
        raise HTTPException(409, "You have already reported this listing")
    db.add(ListingFlag(listing_id=listing_id, tenant_id=user.id, reason=body.reason, notes=body.notes))
    db.flush()
    count = db.scalar(select(func.count()).select_from(ListingFlag).where(ListingFlag.listing_id == listing_id))
    if count >= settings.flags_before_review:
        listing.status = ListingStatus.under_review
    db.commit()
    return {"message": "Thanks, we'll look into it", "hidden_for_review": listing.status == ListingStatus.under_review}
