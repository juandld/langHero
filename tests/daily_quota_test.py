"""Daily per-user caps on imports and uncached TTS (backend/daily_quota.py)."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

import config
import daily_quota
import providers

EMAIL = "cf-access-authenticated-user-email"
IMPORT_BODY = {"text": "A stranger approaches.", "max_scenes": 1, "attest_rights": True}
DAY_ONE = datetime(2026, 11, 26, 23, 0, tzinfo=timezone.utc)
DAY_TWO = datetime(2026, 11, 27, 0, 30, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def quota_env(tmp_path: Path, monkeypatch):
    """Enable the caps with small limits, a private sqlite file, a fixed clock, and no per-minute limiter."""
    monkeypatch.setattr(daily_quota, "DB_PATH", tmp_path / "daily_quota.sqlite")
    monkeypatch.setattr(daily_quota, "_now", lambda: DAY_ONE)
    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(config, "RATE_LIMIT_IMPORT_PER_MIN", 1000)
    monkeypatch.setattr(config, "DAILY_IMPORT_LIMIT", 2)
    monkeypatch.setattr(config, "DAILY_TTS_CLIP_LIMIT", 2)
    return tmp_path / "daily_quota.sqlite"


def _import(client, email: str | None = None):
    headers = {EMAIL: email} if email else {}
    return client.post("/api/stories/import", json=IMPORT_BODY, headers=headers)


def test_import_under_cap_then_over_cap_returns_429(app_client):
    assert _import(app_client, "alice@example.com").status_code == 200
    assert _import(app_client, "alice@example.com").status_code == 200
    res = _import(app_client, "alice@example.com")
    assert res.status_code == 429
    assert res.json() == {"detail": "daily_limit"}


def test_two_emails_are_counted_separately(app_client):
    assert _import(app_client, "alice@example.com").status_code == 200
    assert _import(app_client, "alice@example.com").status_code == 200
    assert _import(app_client, "alice@example.com").status_code == 429
    assert _import(app_client, "bob@example.com").status_code == 200


def test_request_without_email_is_one_shared_anonymous_user(app_client):
    assert _import(app_client).status_code == 200
    assert _import(app_client).status_code == 200
    assert _import(app_client).status_code == 429
    # The anonymous bucket is shared with an explicit blank header.
    assert _import(app_client, "   ").status_code == 429


def test_generation_routes_share_the_import_bucket(app_client):
    headers = {EMAIL: "alice@example.com"}
    assert _import(app_client, "alice@example.com").status_code == 200
    assert _import(app_client, "alice@example.com").status_code == 200
    # Every route in the paywall set is charged against the same daily import bucket.
    auto = app_client.post(
        "/api/import/auto",
        json={"text": "A stranger approaches.", "max_scenes": 1, "attest_rights": True},
        headers=headers,
    )
    assert auto.status_code == 429 and auto.json() == {"detail": "daily_limit"}
    narrative = app_client.post("/api/narratives/generate", json={"items": []}, headers=headers)
    assert narrative.status_code == 429 and narrative.json() == {"detail": "daily_limit"}
    panels = app_client.post(
        "/api/panels/generate-images", json={"panels": [{"type": "full"}]}, headers=headers
    )
    assert panels.status_code == 429 and panels.json() == {"detail": "daily_limit"}


def test_cap_resets_on_next_utc_day(app_client, monkeypatch):
    _import(app_client, "alice@example.com")
    _import(app_client, "alice@example.com")
    assert _import(app_client, "alice@example.com").status_code == 429
    monkeypatch.setattr(daily_quota, "_now", lambda: DAY_TWO)
    assert _import(app_client, "alice@example.com").status_code == 200


def test_counts_persist_in_sqlite_across_process_state(app_client, quota_env):
    _import(app_client, "alice@example.com")
    _import(app_client, "alice@example.com")
    # Read the file directly with a fresh connection, as a restarted backend would.
    conn = sqlite3.connect(quota_env)
    try:
        row = conn.execute(
            "SELECT count FROM daily_usage WHERE user = ? AND bucket = ?",
            ("alice@example.com", daily_quota.BUCKET_GENERATION),
        ).fetchone()
    finally:
        conn.close()
    assert row == (2,)


def test_disabled_flag_leaves_behaviour_unchanged(app_client, monkeypatch, quota_env):
    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", False)
    for _ in range(4):
        assert _import(app_client, "alice@example.com").status_code == 200
    assert not quota_env.exists()


def test_tts_counts_only_uncached_clips(app_client, monkeypatch):
    calls: list[str] = []

    def counting_tts(text: str, voice: str = "alloy", fmt: str = "mp3", instructions=None) -> bytes:
        calls.append(text)
        return f"audio:{len(calls)}".encode("utf-8")

    monkeypatch.setattr(providers, "tts_with_openai", counting_tts, raising=False)

    # Unique phrases so the shared clip cache from other tests cannot make these cache hits.
    phrases = [f"quota {uuid.uuid4().hex}" for _ in range(3)]
    payload = {"language": "English", "provider": "openai", "text": phrases[0]}

    headers = {EMAIL: "alice@example.com"}
    assert app_client.post("/api/tts", json=payload, headers=headers).status_code == 200
    # Same clip again is served from cache and is not charged.
    assert app_client.post("/api/tts", json=payload, headers=headers).status_code == 200
    assert len(calls) == 1

    payload["text"] = phrases[1]
    assert app_client.post("/api/tts", json=payload, headers=headers).status_code == 200

    payload["text"] = phrases[2]
    res = app_client.post("/api/tts", json=payload, headers=headers)
    # The quota error must escape the route's error-swallowing fallback as a 429, not a 200 {"error"}.
    assert res.status_code == 429
    assert res.json() == {"detail": "daily_limit"}
    assert len(calls) == 2

    # Another user has their own allowance.
    payload["text"] = phrases[2]
    res = app_client.post("/api/tts", json=payload, headers={EMAIL: "bob@example.com"})
    assert res.status_code == 200
    assert len(calls) == 3


def test_charge_without_request_context_is_free(quota_env):
    """Batch scripts call the providers outside any request: nothing is charged, nothing is written."""
    token = daily_quota.current_user.set(None)
    try:
        for _ in range(5):
            daily_quota.charge_tts_clip()
    finally:
        daily_quota.current_user.reset(token)
    assert not quota_env.exists()


def test_tts_disabled_flag_does_not_cap(app_client, monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", False)
    calls: list[str] = []

    def counting_tts(text: str, voice: str = "alloy", fmt: str = "mp3", instructions=None) -> bytes:
        calls.append(text)
        return b"audio"

    monkeypatch.setattr(providers, "tts_with_openai", counting_tts, raising=False)
    for _ in range(3):
        payload = {"language": "English", "provider": "openai", "text": f"off {uuid.uuid4().hex}"}
        assert app_client.post("/api/tts", json=payload).status_code == 200
    assert len(calls) == 3
