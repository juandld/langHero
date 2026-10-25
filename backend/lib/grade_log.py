"""SQLite-backed log of Jev grade calls.

One row per bundled Jev call (state sent, scores returned, latency), queryable
by grader name and time range — so questions like "ch1 panels with register
< 0.5 in the last week" become one SELECT. The log must never block or raise
into the practice route: `log_grade` swallows every exception.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parent.parent / "storage" / "grades.sqlite"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    c.execute(
        """CREATE TABLE IF NOT EXISTS jev_grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            grader TEXT NOT NULL,
            target_language TEXT,
            state_json TEXT NOT NULL,
            scores_json TEXT NOT NULL,
            latency_ms REAL
        )"""
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_jev_grades_ts_grader ON jev_grades(ts, grader)")
    return c


def log_grade(
    *,
    grader: str,
    target_language: str | None,
    state: dict[str, Any],
    scores: dict[str, float],
    latency_ms: float,
) -> None:
    try:
        c = _conn()
        c.execute(
            "INSERT INTO jev_grades (ts, grader, target_language, state_json, scores_json, latency_ms) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                grader,
                target_language,
                json.dumps(state, ensure_ascii=False),
                json.dumps(scores, ensure_ascii=False),
                latency_ms,
            ),
        )
        c.close()
    except Exception:
        pass
