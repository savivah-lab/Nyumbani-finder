from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..deps import require_role
from ..models import Listing, ListingFlag, ListingStatus, Payment, PaymentStatus, PaymentType, Role, User
from ..schemas import ListingOut
from ..services.listings import serialize

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_role(Role.admin))])


@router.get("/listings", response_model=list[ListingOut])
def list_by_status(status: ListingStatus = ListingStatus.under_review, limit: int = Query(50, le=200),
                   db: Session = Depends(get_db), admin: User = Depends(require_role(Role.admin))):
    rows = db.scalars(select(Listing).options(selectinload(Listing.photos))
                      .where(Listing.status == status).order_by(Listing.created_at.desc()).limit(limit)).all()
    return [serialize(l, admin, set()) for l in rows]


@router.post("/listings/{listing_id}/status", response_model=ListingOut)
def set_status(listing_id: int, status: ListingStatus, db: Session = Depends(get_db),
               admin: User = Depends(require_role(Role.admin))):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    listing.status = status
    db.commit()
    db.refresh(listing)
    return serialize(listing, admin, set())


@router.get("/listings/{listing_id}/flags")
def listing_flags(listing_id: int, db: Session = Depends(get_db)):
    flags = db.scalars(select(ListingFlag).where(ListingFlag.listing_id == listing_id)).all()
    return [{"tenant_id": f.tenant_id, "reason": f.reason, "notes": f.notes, "created_at": f.created_at} for f in flags]


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    def revenue(t: PaymentType) -> float:
        return float(db.scalar(select(func.coalesce(func.sum(Payment.amount), 0)).where(
            Payment.type == t, Payment.status == PaymentStatus.success)))
    by_status = dict(db.execute(select(Listing.status, func.count()).group_by(Listing.status)).all())
    return {
        "users": db.scalar(select(func.count()).select_from(User)),
        "listings_by_status": {k.value: v for k, v in by_status.items()},
        "revenue_kes": {"listing_fees": revenue(PaymentType.listing_fee), "unlock_fees": revenue(PaymentType.unlock_fee)},
    }
