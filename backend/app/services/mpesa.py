"""M-Pesa Daraja STK Push wrapper. Runs in MOCK mode when no credentials are configured."""
import base64
import uuid
from dataclasses import dataclass
from datetime import datetime

import httpx

from ..config import get_settings

settings = get_settings()

BASE_URLS = {"sandbox": "https://sandbox.safaricom.co.ke", "production": "https://api.safaricom.co.ke"}


class MpesaError(Exception):
    pass


def _base() -> str:
    return BASE_URLS.get(settings.mpesa_env, BASE_URLS["sandbox"])


def _access_token() -> str:
    r = httpx.get(
        f"{_base()}/oauth/v1/generate?grant_type=client_credentials",
        auth=(settings.mpesa_consumer_key, settings.mpesa_consumer_secret),
        timeout=15,
    )
    if r.status_code != 200:
        raise MpesaError("Could not authenticate with M-Pesa")
    return r.json()["access_token"]


def stk_push(phone: str, amount: int, account_ref: str, description: str) -> str:
    """Prompts the customer's phone for their M-Pesa PIN. Returns CheckoutRequestID."""
    if settings.mpesa_mock:
        if not settings.mock_enabled:
            raise MpesaError("Payments are not set up yet. Please try again later.")
        return f"MOCK-{uuid.uuid4().hex[:16]}"

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{settings.mpesa_shortcode}{settings.mpesa_passkey}{timestamp}".encode()).decode()
    payload = {
        "BusinessShortCode": settings.mpesa_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone,
        "PartyB": settings.mpesa_shortcode,
        "PhoneNumber": phone,
        "CallBackURL": f"{settings.mpesa_callback_base_url}/api/payments/mpesa/callback?secret={settings.mpesa_callback_secret}",
        "AccountReference": account_ref[:12],
        "TransactionDesc": description[:13],
    }
    try:
        r = httpx.post(
            f"{_base()}/mpesa/stkpush/v1/processrequest",
            json=payload,
            headers={"Authorization": f"Bearer {_access_token()}"},
            timeout=20,
        )
    except httpx.HTTPError as e:
        raise MpesaError("M-Pesa is unreachable, please try again") from e
    data = r.json()
    if r.status_code != 200 or data.get("ResponseCode") != "0":
        raise MpesaError(data.get("errorMessage") or data.get("ResponseDescription") or "M-Pesa rejected the request")
    return data["CheckoutRequestID"]


@dataclass
class CallbackResult:
    checkout_request_id: str
    success: bool
    receipt: str | None
    amount: float | None
    reason: str | None


def parse_callback(body: dict) -> CallbackResult:
    cb = body["Body"]["stkCallback"]
    items = {i["Name"]: i.get("Value") for i in cb.get("CallbackMetadata", {}).get("Item", [])}
    ok = cb.get("ResultCode") == 0
    return CallbackResult(
        checkout_request_id=cb["CheckoutRequestID"],
        success=ok,
        receipt=items.get("MpesaReceiptNumber"),
        amount=items.get("Amount"),
        reason=None if ok else cb.get("ResultDesc"),
    )
