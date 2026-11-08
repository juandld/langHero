"""Thin stdlib-only client for the nh-backend /api/telegram-out/send endpoint.

Cron scripts (uptime_probe, render_edit_runner, sidekick_auto_merge, etc.)
run as claude-user without Docker/Python-path access to backend/core. They
POST here instead — the gateway then handles dedup, rate-caps, batching,
and the persistent outbox log.

Usage:
    from lib.telegram_out import send
    ok = send(source="uptime_probe", priority="critical",
              text="share api DOWN for 3 minutes",
              dedup_key="uptime:share_api:down")
    # ok is True on 'sent'/'batched'/'queued', False on failure/dedup/rate-cap.

The endpoint is on localhost only — no auth required, but the URL can be
overridden via TELEGRAM_OUT_URL env if the backend moves.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

DEFAULT_URL = "http://localhost:8000/api/telegram-out/send"
DEFAULT_TIMEOUT = 8  # seconds


def send(
    *,
    source: str,
    priority: str,   # 'critical' | 'digestable' | 'dashboard_only'
    text: str,
    dedup_key: str,
    chat_id: int | None = None,
    item_ref: str | None = None,
    parse_mode: str | None = None,
    url: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> bool:
    """POST to /api/telegram-out/send. Returns True if the gateway accepted."""
    body = {
        "source": source, "priority": priority, "text": text,
        "dedup_key": dedup_key,
    }
    if chat_id is not None:
        body["chat_id"] = int(chat_id)
    if item_ref is not None:
        body["item_ref"] = str(item_ref)
    if parse_mode is not None:
        body["parse_mode"] = parse_mode
    req = urllib.request.Request(
        (url or os.getenv("TELEGRAM_OUT_URL") or DEFAULT_URL),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        print(f"[telegram_out] HTTP {exc.code}: {exc.read()[:200]!r}", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"[telegram_out] {type(exc).__name__}: {exc}", file=sys.stderr)
        return False
    status = str(data.get("status") or "")
    return status in ("sent", "batched", "queued")
