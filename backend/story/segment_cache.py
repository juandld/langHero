"""
Segment Cache — file-based JSON caching for generated bridge panels.

Cache key: {story_id}/{from_anchor}->{to_anchor}/{state_hash}

State hash groups players by dominant category + recent 3 choices,
maximizing cache hits for similar play-throughs.
"""

import hashlib
import json
import os
import time
from typing import Optional

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "story_cache")


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def compute_state_hash(player_state: dict) -> str:
    """Compute a cache-friendly hash from player state.

    Groups players by dominant category + last 3 branch choices,
    not exact reputation numbers, to maximize cache hits.
    """
    reputation = player_state.get("reputation", {})
    branch_history = player_state.get("branch_history", [])

    # Dominant category
    dominant = "pragmatic"
    if reputation:
        dominant = max(reputation, key=lambda k: reputation.get(k, 0))

    # Last 3 choices (category only)
    recent = [entry.get("category", "unknown") for entry in branch_history[-3:]]

    key_parts = [dominant] + recent
    key_str = "|".join(key_parts)
    return hashlib.sha256(key_str.encode()).hexdigest()[:12]


def cache_key(story_id: str, from_anchor: str, to_anchor: str, state_hash: str) -> str:
    """Build a filesystem-safe cache key."""
    return f"{story_id}__{from_anchor}__{to_anchor}__{state_hash}"


def get_cached(story_id: str, from_anchor: str, to_anchor: str, state_hash: str) -> Optional[list[dict]]:
    """Retrieve cached panels if they exist."""
    _ensure_cache_dir()
    key = cache_key(story_id, from_anchor, to_anchor, state_hash)
    path = os.path.join(CACHE_DIR, f"{key}.json")

    if not os.path.exists(path):
        return None

    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data.get("panels")
    except (json.JSONDecodeError, OSError):
        return None


def set_cached(story_id: str, from_anchor: str, to_anchor: str, state_hash: str, panels: list[dict]):
    """Store generated panels in cache."""
    _ensure_cache_dir()
    key = cache_key(story_id, from_anchor, to_anchor, state_hash)
    path = os.path.join(CACHE_DIR, f"{key}.json")

    data = {
        "story_id": story_id,
        "from_anchor": from_anchor,
        "to_anchor": to_anchor,
        "state_hash": state_hash,
        "panels": panels,
        "created_at": time.time(),
    }

    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
