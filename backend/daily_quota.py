"""Per-user daily cap on AI-costly actions: story/video imports, generation routes, uncached TTS.

Only enforced when RATE_LIMIT_ENABLED is on (otherwise every call is a no-op). The caller is
identified by the Cloudflare Access email header; a request without one is counted as the shared
"anonymous" user. Counts live in a sqlite file so they survive a backend restart. Days are UTC.

Two entry points:
- `enforce_generation_limit(request)` for the import/generation routes: raises HTTP 429.
- `charge_tts_clip()` at the provider cache-miss points. It reads the user from `current_user`,
  which the /api/tts route sets. Outside a request (batch scripts) it is None and nothing is charged.
  It raises DailyLimitExceeded, a plain exception, so the provider fallback chain must re-raise it.
"""

from __future__ import annotations

import contextvars
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException

import config

DB_PATH = Path(__file__).resolve().parent / "storage" / "daily_quota.sqlite"
EMAIL_HEADER = "cf-access-authenticated-user-email"
ANONYMOUS = "anonymous"

BUCKET_GENERATION = "generation"  # import + generation routes share one bucket
BUCKET_TTS_CLIP = "tts_clip"

current_user: contextvars.ContextVar[str | None] = contextvars.ContextVar("daily_quota_user", default=None)

_lock = threading.Lock()


class DailyLimitExceeded(Exception):
    """The caller has used up today's allowance for this bucket."""


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    c.execute(
        """CREATE TABLE IF NOT EXISTS daily_usage (
            day TEXT NOT NULL,
            user TEXT NOT NULL,
            bucket TEXT NOT NULL,
            count INTEGER NOT NULL,
            PRIMARY KEY (day, user, bucket)
        )"""
    )
    return c


def user_from_request(request) -> str:
    email = (request.headers.get(EMAIL_HEADER) or "").strip().lower()
    return email or ANONYMOUS


def charge(bucket: str, user: str, limit: int) -> None:
    """Count one unit for (today, user, bucket). Raises DailyLimitExceeded when over `limit`."""
    if not config.RATE_LIMIT_ENABLED:
        return
    if limit <= 0:
        return
    day = _now().strftime("%Y-%m-%d")
    with _lock:
        c = _conn()
        try:
            # BEGIN IMMEDIATE takes the write lock, so the check and the increment are atomic across processes too.
            c.execute("BEGIN IMMEDIATE")
            row = c.execute(
                "SELECT count FROM daily_usage WHERE day = ? AND user = ? AND bucket = ?",
                (day, user, bucket),
            ).fetchone()
            count = (row[0] if row else 0) + 1
            if count > limit:
                raise DailyLimitExceeded(f"{bucket} daily limit {limit} reached for {user}")
            c.execute(
                """INSERT INTO daily_usage (day, user, bucket, count) VALUES (?, ?, ?, ?)
                   ON CONFLICT (day, user, bucket) DO UPDATE SET count = excluded.count""",
                (day, user, bucket, count),
            )
            c.execute("COMMIT")
        except BaseException:
            if c.in_transaction:
                c.execute("ROLLBACK")
            raise
        finally:
            c.close()


def enforce_generation_limit(request) -> None:
    """Charge one import/generation against the caller's daily cap. HTTP 429 `daily_limit` when over."""
    try:
        charge(BUCKET_GENERATION, user_from_request(request), config.DAILY_IMPORT_LIMIT)
    except DailyLimitExceeded:
        raise HTTPException(status_code=429, detail="daily_limit")


def charge_tts_clip() -> None:
    """Charge one uncached TTS clip to the user bound to the current request, if any."""
    user = current_user.get()
    if user is None:
        return
    charge(BUCKET_TTS_CLIP, user, config.DAILY_TTS_CLIP_LIMIT)
