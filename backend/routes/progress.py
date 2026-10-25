"""Progress sync endpoint — per-user, per-story.

Lets a learner's save survive across devices and reloads. Minimal shape: JSON
blob in, JSON blob out, keyed by (user_id, story_id). The frontend decides what
goes in; the backend treats it as opaque. One SQLite table alongside grades.sqlite.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/progress", tags=["progress"])

DB_PATH = Path(__file__).resolve().parent.parent / "storage" / "progress.sqlite"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    c.execute(
        """CREATE TABLE IF NOT EXISTS story_progress (
            user_id TEXT NOT NULL,
            story_id TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            updated_ts TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, story_id)
        )"""
    )
    return c


@router.get("/{user_id}/{story_id}")
async def load_progress(user_id: str, story_id: str) -> dict[str, Any]:
    c = _conn()
    row = c.execute(
        "SELECT payload_json, updated_ts FROM story_progress WHERE user_id = ? AND story_id = ?",
        (user_id, story_id),
    ).fetchone()
    c.close()
    if not row:
        raise HTTPException(status_code=404, detail="no progress saved for this (user, story)")
    payload, updated_ts = row
    data = json.loads(payload)
    data["_updated_ts"] = updated_ts
    return data


@router.post("/{user_id}/{story_id}")
async def save_progress(user_id: str, story_id: str, payload: dict[str, Any]) -> dict:
    c = _conn()
    c.execute(
        """INSERT INTO story_progress (user_id, story_id, payload_json, updated_ts)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(user_id, story_id) DO UPDATE SET
               payload_json = excluded.payload_json,
               updated_ts   = datetime('now')""",
        (user_id, story_id, json.dumps(payload, ensure_ascii=False)),
    )
    c.close()
    return {"ok": True, "user_id": user_id, "story_id": story_id}
