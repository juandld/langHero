"""
Security helpers for rate limiting, admin authentication, and user authorization.
"""

import time
from typing import Optional
from fastapi import HTTPException
import config
import auth


# Rate limiting state: bucket -> {ip: (minute_bucket, count)}
_RATE_STATE: dict[str, dict[str, tuple[int, int]]] = {}


def client_ip_from_headers(headers: dict) -> str:
    """Extract client IP from X-Forwarded-For header or return 'unknown'."""
    try:
        xff = headers.get("x-forwarded-for") or headers.get("X-Forwarded-For") or ""
        if isinstance(xff, str) and xff.strip():
            return xff.split(",")[0].strip()
    except Exception:
        pass
    return "unknown"


def rate_limit(bucket: str, ip: str, limit_per_min: int) -> None:
    """Enforce per-minute rate limit. Raises HTTPException(429) if exceeded."""
    if not config.RATE_LIMIT_ENABLED:
        return
    try:
        limit = int(limit_per_min)
    except Exception:
        limit = 0
    if limit <= 0:
        return

    now_bucket = int(time.time() // 60)
    bucket_map = _RATE_STATE.setdefault(bucket, {})
    prev = bucket_map.get(ip)

    if not prev or prev[0] != now_bucket:
        bucket_map[ip] = (now_bucket, 1)
        return

    count = int(prev[1]) + 1
    bucket_map[ip] = (now_bucket, count)

    if count > limit:
        raise HTTPException(status_code=429, detail="rate_limited")


def is_admin(headers: dict) -> bool:
    """Check if request has valid admin credentials via X-Admin-Key or Bearer token."""
    key = (config.ADMIN_API_KEY or "").strip()
    if not key:
        return False

    # Accept X-Admin-Key header
    try:
        supplied = headers.get("x-admin-key") or headers.get("X-Admin-Key") or ""
        if isinstance(supplied, str) and supplied.strip() == key:
            return True
    except Exception:
        pass

    # Accept Authorization: Bearer <key>
    try:
        auth_header = headers.get("authorization") or headers.get("Authorization") or ""
        if isinstance(auth_header, str) and auth_header.lower().startswith("bearer "):
            token = auth_header.split(None, 1)[1].strip()
            if token == key:
                return True
    except Exception:
        pass

    return False


def require_admin(headers: dict, *, flag: bool) -> None:
    """Require admin authentication if flag is True. Raises HTTPException on failure."""
    if not flag:
        return
    if not (config.ADMIN_API_KEY or "").strip():
        raise HTTPException(status_code=500, detail="admin_key_not_configured")
    if not is_admin(headers):
        raise HTTPException(status_code=401, detail="admin_required")


async def require_auth(headers: dict, *, payload: Optional[dict] = None, flag: bool) -> None:
    """Require user authentication if flag is True. Raises HTTPException on failure."""
    if not flag:
        return
    try:
        await auth.require_user(headers, payload=payload, required=True)
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def normalize_headers(request) -> dict:
    """Normalize request headers to lowercase keys."""
    return {k.lower(): v for (k, v) in request.headers.items()}


def extract_client_ip(request, headers: dict) -> str:
    """Extract client IP from the request object, falling back to headers."""
    return (request.client.host if request.client else None) or client_ip_from_headers(headers)


async def request_guard(
    request,
    *,
    admin_flag: bool = False,
    auth_flag: bool = False,
    rate_bucket: str,
    rate_limit_per_min: int = 10,
) -> dict:
    """Common request validation: normalize headers, check admin/auth, rate-limit.

    Returns the normalized headers dict for further use by the caller.
    """
    headers = normalize_headers(request)
    require_admin(headers, flag=admin_flag)
    await require_auth(headers, flag=auth_flag)
    ip = extract_client_ip(request, headers)
    rate_limit(rate_bucket, str(ip), rate_limit_per_min)
    return headers


async def parse_json_body(request) -> dict:
    """Safely parse JSON body from a request, returning empty dict on failure."""
    try:
        return await request.json()
    except Exception:
        return {}


def detect_audio_mime(content_type: str) -> str:
    """Detect audio MIME type from an upload's content_type string."""
    ct = (content_type or '').lower()
    if 'webm' in ct:
        return 'audio/webm'
    if 'ogg' in ct:
        return 'audio/ogg'
    if 'm4a' in ct:
        return 'audio/mp4'
    if 'mp3' in ct:
        return 'audio/mp3'
    return 'audio/wav'


def clean_llm_json(raw: str) -> str:
    """Strip markdown code fences from LLM JSON responses."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return cleaned
