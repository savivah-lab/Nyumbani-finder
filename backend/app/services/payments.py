"""Shared payment settlement logic, used by both the M-Pesa callback and the mock completer."""
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import Listing, ListingStatus, Payment, PaymentStatus, PaymentType, Unlock, utcnow

settings = get_settings()


def settle_payment(db: Session, payment: Payment, success: bool, receipt: str | None = None,
                   paid_amount: float | None = None, reason: str | None = None) -> Payment:
    """Idempotent: safe if M-Pesa retries the callback."""
    if payment.status != PaymentStatus.pending:
        return payment

    if success and paid_amount is not None and float(paid_amount) < float(payment.amount):
        success, reason = False, f"Underpaid: expected {payment.amount}, got {paid_amount}"

    if not success:
        payment.status = PaymentStatus.failed
        payment.failure_reason = (reason or "Payment failed")[:255]
        db.commit()
        return payment

    payment.status = PaymentStatus.success
    payment.mpesa_receipt = receipt
    listing = db.get(Listing, payment.listing_id)

    if payment.type == PaymentType.listing_fee:
        if listing.status in (ListingStatus.pending, ListingStatus.expired):
            listing.status = ListingStatus.active
            listing.expires_at = utcnow() + timedelta(days=settings.listing_expiry_days)
    elif payment.type == PaymentType.unlock_fee:
        exists = db.scalar(select(Unlock).where(Unlock.tenant_id == payment.user_id, Unlock.listing_id == payment.listing_id))
        if not exists:
            db.add(Unlock(tenant_id=payment.user_id, listing_id=payment.listing_id, payment_id=payment.id))
    db.commit()
    return payment


def expire_listings(db: Session) -> int:
    rows = db.scalars(
        select(Listing).where(Listing.status == ListingStatus.active, Listing.expires_at < utcnow())
    ).all()
    for l in rows:
        l.status = ListingStatus.expired
    db.commit()
    return len(rows)
