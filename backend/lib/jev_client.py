"""Canonical Jev API client for host-side callers (scripts, skills, cron).

Wraps `POST https://api.typesafe.ai/v1/systemone` with:

  * Fault detection — auth/quota/rate-limit/network split.
  * Telegram alerts via `scripts/lib/telegram_out.py` on fault types
    that need David's attention (recharge, expired key). Dedup per
    fault type via the gateway's 24h window; no local dedup file.
  * Automatic retry with exponential backoff on transient failures
    (network, 5xx, and even 429 — a couple times before giving up).
  * TYPESAFE_API_KEY loaded from env or crankHero/.env, cached per process.

Usage:
    from lib.jev_client import call, JevError, JevAuthError, JevQuotaError

    try:
        answers = call(state={"topic": "...", "paragraph": "..."},
                       questions={"is_urgent": {"type": "noul", "instructions": "..."}})
    except JevQuotaError:
        # never reached — the client already Telegram-alerted David; caller
        # sees a normal exception and can back off.
        raise

# TODO: extract to shared heroes-jev package (copied from
# orchestratorHero/scripts/lib/jev_client.py for langHero/practice MVP).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

from lib import telegram_out  # noqa: E402

CRANKHERO_ENV = Path(os.environ.get("PROJECTS_DIR", "/home/claude-user/projects")) / "crankHero" / ".env"
API_URL = "https://api.typesafe.ai/v1/systemone"
DEFAULT_MODEL = "jev-latest"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
CONSOLE_URL = "https://console.typesafe.ai"
KEYS_URL = "https://console.typesafe.ai/keys"
BILLING_URL = "https://console.typesafe.ai/settings/billing"

_cached_key: str | None = None

# In-process response cache for identical (state, questions, model) triples.
# Jev scores are deterministic within a model version (empirically verified in
# the capability probe: three identical calls returned 0.06 / 0.06 / 0.05), so
# caching is safe and cuts repeat lookups from ~60ms to microseconds. Bounded
# via FIFO eviction at CACHE_MAX to keep memory flat under scanner workloads.
_response_cache: dict[str, dict] = {}
_response_cache_order: list[str] = []
CACHE_MAX = 2000


def _cache_key(state: Any, questions: dict, model: str) -> str:
    src = json.dumps({"s": state, "q": questions, "m": model}, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(src.encode("utf-8")).hexdigest()


def _cache_put(key: str, answers: dict) -> None:
    if key in _response_cache:
        return
    _response_cache[key] = answers
    _response_cache_order.append(key)
    if len(_response_cache_order) > CACHE_MAX:
        oldest = _response_cache_order.pop(0)
        _response_cache.pop(oldest, None)


class JevError(Exception):
    """Base — any Jev call that could not be fulfilled."""


class JevAuthError(JevError):
    """401/403 — expired or missing API key."""


class JevQuotaError(JevError):
    """402 Payment Required — free tokens exhausted, recharge needed."""


class JevRateLimitError(JevError):
    """429 Too Many Requests — sustained after retries."""


class JevServerError(JevError):
    """5xx after retries."""


class JevNetworkError(JevError):
    """Connection/timeout after retries."""


def _load_key() -> str:
    global _cached_key
    if _cached_key:
        return _cached_key
    k = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not k and CRANKHERO_ENV.exists():
        for line in CRANKHERO_ENV.read_text().splitlines():
            if line.strip().startswith("TYPESAFE_API_KEY="):
                k = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    if not k:
        _alert("missing_key", "TYPESAFE_API_KEY not set in env or crankHero/.env. Cannot call Jev.")
        raise JevAuthError("TYPESAFE_API_KEY not configured")
    _cached_key = k
    return k


JEV_LISTENER_SESSION = os.environ.get(
    "JEV_LISTENER_SESSION",
    "c7506826-a299-4a8a-bd8f-30052bc96f76",
)
SECRETARY_URL = os.environ.get("LLMT_SECRETARY_URL", "http://localhost:8000/api/secretary/items")


def _alert(kind: str, msg: str, extra_url: str | None = None) -> None:
    """Send a critical Telegram alert AND light up the Jev-listener session's
    NEEDS YOU. Deduped per (source=jev_watchdog, dedup_key=jev:<kind>) within 24h."""
    body = f"⚠ Jev API problem ({kind}):\n{msg}"
    if extra_url:
        body += f"\n\nAction: {extra_url}"
    try:
        telegram_out.send(
            source="jev_watchdog",
            priority="critical",
            text=body,
            dedup_key=f"jev:{kind}",
        )
    except Exception as e:
        print(f"[jev_client] telegram alert failed: {e}", file=sys.stderr)
    # Also route to NEEDS YOU via secretary — brings the Jev rollout chat back into focus.
    try:
        import json as _json
        secretary_body = _json.dumps({
            "source_type": "session",
            "source_id": JEV_LISTENER_SESSION,
            "title": f"Jev API problem: {kind}",
            "observation": msg[:1000],
            "opinion": "",
            "ask": f"Take action at {extra_url}" if extra_url else "Investigate the Jev API problem.",
            "urgency": "high",
            "action_url": f"/terminal/#{JEV_LISTENER_SESSION}",
            "attention_minutes": 4,
        })
        req = requests.post(SECRETARY_URL, data=secretary_body, headers={"Content-Type": "application/json"}, timeout=5)
        req.raise_for_status()
    except Exception as e:
        print(f"[jev_client] secretary post failed: {e}", file=sys.stderr)


def call(
    state: Any,
    questions: dict,
    *,
    api_key: str | None = None,
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> dict:
    """Return the `answers` dict from Jev. Raises a specific JevError on failure
    (and Telegram-alerts David for auth / quota / rate-limit / network faults).
    """
    cache_key = _cache_key(state, questions, model)
    cached = _response_cache.get(cache_key)
    if cached is not None:
        return cached

    key = api_key or _load_key()
    payload = {"state": state, "model": model, "questions": questions}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=timeout)
        except requests.exceptions.RequestException as e:
            last_exc = e
            if attempt < max_retries:
                time.sleep(min(2 ** (attempt - 1), 10))
                continue
            _alert("network", f"Jev unreachable after {max_retries} attempts: {type(e).__name__}: {e}")
            raise JevNetworkError(str(e)) from e

        # Auth: never retry
        if r.status_code in (401, 403):
            _alert(
                "auth_failed",
                f"HTTP {r.status_code} — the API key is invalid or revoked. Rotate it.",
                extra_url=KEYS_URL,
            )
            raise JevAuthError(f"HTTP {r.status_code}: {r.text[:200]}")

        # Payment: never retry
        if r.status_code == 402:
            _alert(
                "recharge_needed",
                f"HTTP 402 Payment Required — free tokens exhausted. Add credit to keep Jev working.",
                extra_url=BILLING_URL,
            )
            raise JevQuotaError(f"HTTP 402: {r.text[:200]}")

        # Rate limit: retry a couple times, then alert
        if r.status_code == 429:
            if attempt < max_retries:
                time.sleep(min(2 ** attempt, 30))
                continue
            _alert(
                "rate_limited",
                f"HTTP 429 sustained across {max_retries} retries. Either short-term rate cap or overall usage limit hit.",
                extra_url=BILLING_URL,
            )
            raise JevRateLimitError(f"HTTP 429: {r.text[:200]}")

        # 5xx: retry, then alert
        if r.status_code >= 500:
            if attempt < max_retries:
                time.sleep(min(2 ** (attempt - 1), 10))
                continue
            _alert(
                "server_error",
                f"HTTP {r.status_code} sustained across {max_retries} retries. Typesafe API appears down.",
                extra_url=CONSOLE_URL,
            )
            raise JevServerError(f"HTTP {r.status_code}: {r.text[:200]}")

        # Success path
        if r.status_code == 200:
            try:
                answers = r.json()["answers"]
            except (KeyError, ValueError) as e:
                _alert(
                    "bad_response",
                    f"HTTP 200 but response missing 'answers' key: {r.text[:200]}",
                )
                raise JevError(f"malformed response: {e}") from e
            _cache_put(cache_key, answers)
            return answers

        # Anything else — 4xx that isn't the handled ones
        _alert(
            "http_error",
            f"HTTP {r.status_code}: {r.text[:200]}",
        )
        raise JevError(f"HTTP {r.status_code}: {r.text[:200]}")

    # Unreachable — the loop returns or raises on every path
    raise JevError(f"exhausted retries: {last_exc}")


def diagnostic() -> dict:
    """One-shot sanity check: does the API respond with a valid answer to a
    trivial question? Returns {"ok": bool, "latency_ms": float, "error": str}.
    Useful for a cron heartbeat.
    """
    t0 = time.perf_counter()
    try:
        ans = call(
            state="ping",
            questions={"is_ping": {"type": "noul", "instructions": "This state is the word 'ping'."}},
            max_retries=1,
            timeout=15,
        )
        return {"ok": True, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), "answer": ans.get("is_ping", {}).get("noul")}
    except JevError as e:
        return {"ok": False, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), "error": type(e).__name__, "detail": str(e)}


if __name__ == "__main__":
    # CLI: `python3 lib/jev_client.py` runs a diagnostic.
    result = diagnostic()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["ok"] else 1)
