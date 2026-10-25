"""Observability read endpoints — grades browsing + roll-ups.

Thin wrapper over backend/storage/grades.sqlite. Read-only; nothing to mutate.
Served David-only via the Cloudflare Access + nginx guard the project already
has — no auth logic here.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/observability", tags=["observability"])

DB_PATH = Path(__file__).resolve().parent.parent / "storage" / "grades.sqlite"


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@router.get("/grades")
def recent_grades(
    grader: str | None = Query(None, description="filter by grader name"),
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, Any]:
    """Return the most recent grade rows (newest first).

    Each row surfaces: id, ts, grader, target_language, scores (dict),
    latency_ms, and the state fields callers tend to want (tutor_line,
    source_id, scenario, speaker). Full state_json is omitted — fetch
    one row's detail with /grades/{id} if needed.
    """
    if not DB_PATH.exists():
        return {"rows": [], "total": 0}
    where = "1=1"
    params: list[Any] = []
    if grader:
        where += " AND grader = ?"
        params.append(grader)
    c = _conn()
    rows = c.execute(
        f"SELECT id, ts, grader, target_language, state_json, scores_json, latency_ms "
        f"FROM jev_grades WHERE {where} ORDER BY id DESC LIMIT ?",
        (*params, limit),
    ).fetchall()
    total = c.execute(f"SELECT COUNT(*) FROM jev_grades WHERE {where}", params).fetchone()[0]
    c.close()
    out = []
    for rid, ts, g, lang, state_s, scores_s, lat in rows:
        state = json.loads(state_s)
        out.append({
            "id": rid, "ts": ts, "grader": g, "target_language": lang,
            "scores": json.loads(scores_s),
            "latency_ms": lat,
            "tutor_line": state.get("tutor_line", ""),
            "source_id": state.get("source_id"),
            "scenario": state.get("scenario", "")[:120],
            "speaker": state.get("speaker"),
            "session_id": state.get("session_id"),
        })
    return {"rows": out, "total": total}


_timeline_store: dict[str, list[dict]] = {}
_TIMELINE_MAX_PER_SESSION = 5000
_TIMELINE_MAX_SESSIONS = 200
_timeline_order: list[str] = []  # FIFO eviction of session ids


@router.get("/timeline/{session_id}")
def get_timeline(session_id: str) -> dict[str, Any]:
    """Return recorded timeline events for a session (in-memory, bounded)."""
    events = _timeline_store.get(session_id, [])
    return {"session_id": session_id, "events": events, "count": len(events)}


@router.post("/timeline/{session_id}")
def ingest_timeline(session_id: str, batch: dict[str, Any]) -> dict:
    """Append a batch of recorder events to this session's store.

    Body shape: {"events": [{"t_ms": int, "kind": str, "data": any}, ...]}.
    FIFO-evicts oldest session when the registry fills.
    """
    events = batch.get("events") or []
    if not isinstance(events, list):
        return {"ok": False, "error": "events must be a list"}

    if session_id not in _timeline_store:
        if len(_timeline_order) >= _TIMELINE_MAX_SESSIONS:
            oldest = _timeline_order.pop(0)
            _timeline_store.pop(oldest, None)
        _timeline_order.append(session_id)
        _timeline_store[session_id] = []

    bucket = _timeline_store[session_id]
    for e in events:
        if isinstance(e, dict) and "t_ms" in e and "kind" in e:
            bucket.append(e)
    if len(bucket) > _TIMELINE_MAX_PER_SESSION:
        del bucket[: len(bucket) - _TIMELINE_MAX_PER_SESSION]
    return {"ok": True, "total_events": len(bucket)}


def _compute_sync_delays(events: list[dict]) -> list[float]:
    """For each audio_play event, find the most recent preceding anchor within
    10s — audio-smelling fetch_start OR panel_entered — and record the delta.

    fetch_start is the tighter signal (network→audio). panel_entered is the
    fallback for cached-audio paths where no fetch precedes playback.
    """
    delays: list[float] = []
    pending_anchor_ms: float | None = None
    for e in events:
        kind = e.get("kind")
        data = e.get("data") or {}
        if kind == "fetch_start":
            url = str(data.get("url", ""))
            if any(tag in url for tag in ("/tts", "/audio", "/examples", "/narrative")):
                pending_anchor_ms = e.get("t_ms")
        elif kind == "panel_entered":
            # Weaker anchor: only use if no fetch anchor already set.
            if pending_anchor_ms is None:
                pending_anchor_ms = e.get("t_ms")
        elif kind == "audio_play" and pending_anchor_ms is not None:
            delta = float(e.get("t_ms", 0)) - float(pending_anchor_ms)
            if 0 <= delta <= 10000:
                delays.append(round(delta, 1))
            pending_anchor_ms = None
    return delays


@router.get("/sync-stats")
def sync_stats() -> dict[str, Any]:
    """Audio-sync metrics across all captured sessions.

    audio_start_delays_ms: for each matched (fetch_start → audio_play) pair,
    the delay between when the audio-asset request started and when playback
    actually began. 500ms is the project's self-set budget.
    """
    all_delays: list[float] = []
    per_session: dict[str, list[float]] = {}
    for sid, events in _timeline_store.items():
        delays = _compute_sync_delays(events)
        if delays:
            per_session[sid] = delays
            all_delays.extend(delays)
    worst = max(all_delays) if all_delays else None
    median = sorted(all_delays)[len(all_delays) // 2] if all_delays else None
    return {
        "sessions_contributing": len(per_session),
        "sample_count": len(all_delays),
        "audio_start_delays_ms": all_delays,
        "worst_ms": worst,
        "median_ms": median,
        "budget_ms": 500,
    }


@router.get("/grades/stats")
def grade_stats() -> dict[str, Any]:
    """Per-grader counts + rolling averages (last 7 days)."""
    if not DB_PATH.exists():
        return {"by_grader": []}
    c = _conn()
    rows = c.execute(
        """SELECT grader, COUNT(*), AVG(latency_ms)
           FROM jev_grades
           WHERE ts >= datetime('now', '-7 days')
           GROUP BY grader
           ORDER BY grader"""
    ).fetchall()
    out = []
    for g, cnt, lat_avg in rows:
        # Compute dim averages across the last 100 rows per grader
        dim_rows = c.execute(
            "SELECT scores_json FROM jev_grades WHERE grader = ? ORDER BY id DESC LIMIT 100",
            (g,),
        ).fetchall()
        sums = {"register_fits": 0.0, "naturalness": 0.0, "level_appropriate": 0.0}
        n = 0
        for (sj,) in dim_rows:
            s = json.loads(sj)
            for k in sums:
                sums[k] += float(s.get(k, 0) or 0)
            n += 1
        avgs = {k: (v / n if n else 0) for k, v in sums.items()}
        out.append({
            "grader": g, "count_7d": cnt,
            "latency_ms_avg": round(lat_avg or 0, 1),
            "scores_avg_last_100": {k: round(v, 3) for k, v in avgs.items()},
        })
    c.close()
    return {"by_grader": out}
