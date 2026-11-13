import math
import re

EARTH_RADIUS_KM = 6371.0088


def normalize_phone(raw: str) -> str:
    """Normalise Kenyan numbers to 2547XXXXXXXX / 2541XXXXXXXX. Raises ValueError if invalid."""
    digits = re.sub(r"[^\d]", "", raw or "")
    if digits.startswith("0") and len(digits) == 10:
        digits = "254" + digits[1:]
    elif len(digits) == 9 and digits[0] in "71":
        digits = "254" + digits
    if not re.fullmatch(r"254[17]\d{8}", digits):
        raise ValueError("Enter a valid Kenyan phone number, e.g. 0712345678")
    return digits


def mask_phone(phone: str) -> str:
    """Reveal nothing beyond the network prefix, so the number can't be pieced together."""
    return f"0{phone[3]}** *** ***"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def bounding_box(lat: float, lon: float, radius_km: float):
    """Cheap SQL-friendly pre-filter; exact distance is checked afterwards."""
    dlat = math.degrees(radius_km / EARTH_RADIUS_KM)
    dlon = math.degrees(radius_km / (EARTH_RADIUS_KM * max(math.cos(math.radians(lat)), 0.01)))
    return lat - dlat, lat + dlat, lon - dlon, lon + dlon
