"""
Lightweight request-timing tracker.

Records per-endpoint latency in a fixed-size ring buffer so /api/perf
can report real numbers without any external tooling.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Keep the last N request timings in memory.
_MAX_ENTRIES = 500

_ring: deque[Dict[str, Any]] = deque(maxlen=_MAX_ENTRIES)


def record(
    *,
    method: str,
    path: str,
    status: int,
    duration_ms: float,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """Append one timing entry."""
    entry: Dict[str, Any] = {
        "ts": time.time(),
        "method": method,
        "path": path,
        "status": status,
        "ms": round(duration_ms, 1),
    }
    if extra:
        entry.update(extra)
    _ring.append(entry)


def recent(limit: int = 100) -> List[Dict[str, Any]]:
    """Return the most recent *limit* entries (newest first)."""
    items = list(_ring)
    items.reverse()
    return items[:limit]


@dataclass
class _RouteStats:
    count: int = 0
    total_ms: float = 0.0
    min_ms: float = float("inf")
    max_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    _all: list = field(default_factory=list)

    def add(self, ms: float) -> None:
        self.count += 1
        self.total_ms += ms
        if ms < self.min_ms:
            self.min_ms = ms
        if ms > self.max_ms:
            self.max_ms = ms
        self._all.append(ms)

    def finalize(self) -> Dict[str, Any]:
        self._all.sort()
        n = len(self._all)
        self.p50_ms = self._all[n // 2] if n else 0
        self.p95_ms = self._all[int(n * 0.95)] if n else 0
        return {
            "count": self.count,
            "avg_ms": round(self.total_ms / max(1, self.count), 1),
            "min_ms": round(self.min_ms, 1) if self.min_ms != float("inf") else 0,
            "max_ms": round(self.max_ms, 1),
            "p50_ms": round(self.p50_ms, 1),
            "p95_ms": round(self.p95_ms, 1),
        }


def summary() -> Dict[str, Any]:
    """Aggregate stats grouped by route."""
    by_route: Dict[str, _RouteStats] = {}
    for entry in _ring:
        key = f"{entry['method']} {entry['path']}"
        stats = by_route.get(key)
        if stats is None:
            stats = _RouteStats()
            by_route[key] = stats
        stats.add(entry["ms"])

    return {
        route: s.finalize()
        for route, s in sorted(by_route.items(), key=lambda kv: -kv[1].max_ms)
    }
