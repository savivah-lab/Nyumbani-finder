from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..deps import get_current_user, require_role
from ..models import Listing, ListingStatus, Payment, PaymentStatus, PaymentType, Role, Unlock, User
from ..schemas import InitiatePaymentOut, PayIn, PaymentOut
from ..services import mpesa
from ..services.payments import settle_payment

settings = get_settings()
router = APIRouter(prefix="/api/payments", tags=["payments"])


def _start(db: Session, user: User, listing: Listing, ptype: PaymentType, amount: int, phone: str | None) -> Payment:
    """Create a pending payment and trigger the STK push. Reuses an in-flight payment to avoid double charges."""
    existing = db.scalar(select(Payment).where(
        Payment.user_id == user.id, Payment.listing_id == listing.id,
        Payment.type == ptype, Payment.status == PaymentStatus.pending))
    if existing:
        return existing
    payment = Payment(user_id=user.id, listing_id=listing.id, type=ptype, amount=amount,
                      phone_number=phone or user.phone_number)
    db.add(payment)
    db.flush()
    try:
        payment.checkout_request_id = mpesa.stk_push(payment.phone_number, amount, f"NF{listing.id}", ptype.value)
    except mpesa.MpesaError as e:
        db.rollback()
        raise HTTPException(502, str(e))
    db.commit()
    return payment


@router.post("/listing-fee/{listing_id}", response_model=InitiatePaymentOut)
def pay_listing_fee(listing_id: int, body: PayIn, db: Session = Depends(get_db),
                    user: User = Depends(require_role(Role.landlord, Role.admin))):
    listing = db.get(Listing, listing_id)
    if not listing or listing.landlord_id != user.id:
        raise HTTPException(404, "Listing not found")
    if listing.status not in (ListingStatus.pending, ListingStatus.expired):
        raise HTTPException(400, "This listing does not need a listing fee right now")
    if not listing.photos:
        raise HTTPException(400, "Add at least one photo before paying to publish")
    p = _start(db, user, listing, PaymentType.listing_fee, settings.listing_fee, body.phone_number)
    return InitiatePaymentOut(payment=p, message="Check your phone and enter your M-Pesa PIN")


@router.post("/unlock/{listing_id}", response_model=InitiatePaymentOut)
def unlock_contact(listing_id: int, body: PayIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    listing = db.get(Listing, listing_id)
    if not listing or listing.status != ListingStatus.active:
        raise HTTPException(404, "Listing not found")
    if listing.landlord_id == user.id:
        raise HTTPException(400, "This is your own listing")
    if db.scalar(select(Unlock).where(Unlock.tenant_id == user.id, Unlock.listing_id == listing_id)):
        return InitiatePaymentOut(already_unlocked=True, contact_phone=listing.contact_phone,
                                  message="You already unlocked this number - no charge")
    p = _start(db, user, listing, PaymentType.unlock_fee, settings.unlock_fee, body.phone_number)
    return InitiatePaymentOut(payment=p, message="Check your phone and enter your M-Pesa PIN")


@router.get("/{payment_id}", response_model=PaymentOut)
def payment_status(payment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Frontend polls this after the STK push until status is success/failed."""
    p = db.get(Payment, payment_id)
    if not p or (p.user_id != user.id and user.role != Role.admin):
        raise HTTPException(404, "Payment not found")
    return p


@router.post("/mpesa/callback", include_in_schema=False)
async def mpesa_callback(request: Request, secret: str = "", db: Session = Depends(get_db)):
    """Called by Safaricom. Guarded by a shared secret in the URL, and amounts are re-checked."""
    if secret != settings.mpesa_callback_secret:
        raise HTTPException(403, "Forbidden")
    try:
        result = mpesa.parse_callback(await request.json())
    except (KeyError, ValueError):
        return {"ResultCode": 0, "ResultDesc": "Ignored malformed payload"}
    payment = db.scalar(select(Payment).where(Payment.checkout_request_id == result.checkout_request_id))
    if payment:
        settle_payment(db, payment, result.success, result.receipt, result.amount, result.reason)
    return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post("/mock/{payment_id}/complete", response_model=PaymentOut)
def mock_complete(payment_id: int, success: bool = True, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """DEV ONLY: simulates the customer entering (or cancelling) their PIN. Disabled once real M-Pesa creds are set."""
    if not settings.mock_enabled:
        raise HTTPException(404, "Not found")
    p = db.get(Payment, payment_id)
    if not p or p.user_id != user.id:
        raise HTTPException(404, "Payment not found")
    return settle_payment(db, p, success, receipt=f"MOCK{p.id:08d}" if success else None,
                          reason=None if success else "Request cancelled by user")
