"""
Warm the localization cache for all stories so a player's first Spanish
(or other language) chapter load doesn't stall on a live LLM round-trip.

Run against the live backend (it hits the real /api/story-panels endpoints,
same code path as the game):

    python3 backend/scripts/warm_localize_cache.py --language es --level beginner
    python3 backend/scripts/warm_localize_cache.py --language es --level all

Safe to re-run: localize_panels() caches by content hash, so an already-warm
chapter is a no-op fetch, not a repeat LLM call.
"""

import argparse
import sys
import time

import httpx

BASE_URL = "http://127.0.0.1:8100"
ALL_LEVELS = ["beginner", "elementary", "intermediate", "advanced"]


def warm(language: str, levels: list[str]):
    with httpx.Client(timeout=120.0) as client:
        stories = client.get(f"{BASE_URL}/api/story-panels/stories").json()["stories"]
        for story in stories:
            story_id = story["id"]
            for level in levels:
                t0 = time.time()
                resp = client.get(
                    f"{BASE_URL}/api/story-panels/stories/{story_id}",
                    params={"language": language, "level": level},
                )
                resp.raise_for_status()
                elapsed = time.time() - t0
                print(f"[warm] {story_id} language={language} level={level} ({elapsed:.1f}s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--language", default="es")
    parser.add_argument("--level", default="beginner", help="One level, or 'all' for every level")
    args = parser.parse_args()

    levels = ALL_LEVELS if args.level == "all" else [args.level]
    warm(args.language, levels)
