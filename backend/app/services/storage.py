"""Photo storage. Cloudinary when configured (production), local disk otherwise (development)."""
import hashlib
import time
import uuid
from pathlib import Path

import httpx

from fastapi import HTTPException, UploadFile

from ..config import get_settings

settings = get_settings()
MAX_BYTES = 5 * 1024 * 1024
SIGNATURES = {b"\xff\xd8\xff": ".jpg", b"\x89PNG\r\n\x1a\n": ".png", b"RIFF": ".webp"}


def _detect_ext(head: bytes) -> str | None:
    for sig, ext in SIGNATURES.items():
        if head.startswith(sig):
            if ext == ".webp" and head[8:12] != b"WEBP":
                continue
            return ext
    return None


async def save_image(file: UploadFile) -> str:
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"{file.filename}: image is larger than 5MB")
    ext = _detect_ext(data[:12])
    if not ext:  # check real bytes, not the client-declared content type
        raise HTTPException(415, f"{file.filename}: only JPEG, PNG or WebP images are allowed")
    if settings.cloudinary_enabled:
        return _upload_cloudinary(data, file.filename or "photo")
    folder = Path(settings.upload_dir)
    folder.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{ext}"
    (folder / name).write_bytes(data)
    return f"/uploads/{name}"


def _upload_cloudinary(data: bytes, filename: str) -> str:
    """Signed upload straight to Cloudinary's REST API (no SDK needed). Returns an https URL."""
    ts = str(int(time.time()))
    folder = "nyumbani-finder"
    to_sign = f"folder={folder}&timestamp={ts}{settings.cloudinary_api_secret}"
    signature = hashlib.sha1(to_sign.encode()).hexdigest()
    try:
        r = httpx.post(
            f"https://api.cloudinary.com/v1_1/{settings.cloudinary_cloud_name}/image/upload",
            data={"api_key": settings.cloudinary_api_key, "timestamp": ts, "folder": folder, "signature": signature},
            files={"file": (filename, data)},
            timeout=30,
        )
    except httpx.HTTPError:
        raise HTTPException(502, "Photo storage is unreachable, please try again")
    if r.status_code != 200:
        raise HTTPException(502, "Photo storage rejected the upload")
    return r.json()["secure_url"]
