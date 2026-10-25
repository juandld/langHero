"""Idempotent story bootstrap: generate missing character + location
reference images, then (re)generate every panel via the manifest pipeline.

The whole point of the manifest system is character consistency across
panels: a character ref is generated once, then attached as a reference to
every panel the character appears in so the character's face/hair/outfit
stays stable. This script is the single entry point that honors that
contract — nothing here reimplements prompt building; it only orchestrates
calls into story.manifest + story.panels_test + image.google.

Scope today: shogun_test. journey_west port is step 3 of the pipeline
upgrade (requires adding JW_CHARACTERS/JW_LOCATIONS/JW_PANELS to
story.manifest and generalizing generate_panel_from_manifest to take any
manifest dict). Until that lands, journey_west stays on
backend/generate_jw_images.py.

Usage:
    python -m scripts.ensure_story shogun_test [--panels-only] [--refs-only] [--force]

Flags:
    --refs-only   generate missing character + location refs, skip panels
    --panels-only skip ref generation, go straight to panels (useful if you
                  know the refs are already correct and only want to re-roll
                  the panels at the current manifest + prompts)
    --force       re-generate even if the file already exists on disk
                  (applies to refs AND panels when combined)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

from image.google import (  # noqa: E402
    generate_character_ref,
    generate_location_ref,
)
from story.manifest import (  # noqa: E402
    SHOGUN_CHARACTERS,
    SHOGUN_LOCATIONS,
    SHOGUN_PANELS,
)
from story.panels_test import generate_panel_from_manifest  # noqa: E402


STORIES = {
    "shogun_test": {
        "characters": SHOGUN_CHARACTERS,
        "locations": SHOGUN_LOCATIONS,
        "panels": SHOGUN_PANELS,
    },
}


async def ensure_character_refs(characters: dict, force: bool) -> list[dict]:
    """Generate a reference image for each character whose ref_path is
    missing on disk (or if --force, always). Uses the character's own
    `description` field as the generation prompt — no face anchor, no
    hand-tuned per-character prompt — so adding a new character to the
    manifest is enough to get it generated on next run."""
    results = []
    for cid, char in characters.items():
        exists = char.reference_path and os.path.exists(char.reference_path)
        if exists and not force:
            print(f"  CHAR  {cid:16} skip (exists)")
            results.append({"character_id": cid, "cached": True})
            continue
        prompt = (
            f"Character reference sheet, portrait orientation, plain neutral "
            f"background. {char.description} Manhwa / Korean webtoon style, "
            f"clean lineart, consistent lighting. Face and body visible, "
            f"calm neutral expression suitable as a visual reference anchor."
        )
        t0 = time.perf_counter()
        try:
            r = await generate_character_ref(cid, prompt, face_reference=None, force=force)
            dt = time.perf_counter() - t0
            print(f"  CHAR  {cid:16} OK  {dt:>5.1f}s  → {r['path']}")
            results.append(r)
        except Exception as e:
            print(f"  CHAR  {cid:16} FAIL {type(e).__name__}: {str(e)[:140]}")
            results.append({"character_id": cid, "error": str(e)})
    return results


async def ensure_location_refs(locations: dict, force: bool) -> list[dict]:
    """Same as ensure_character_refs but for locations. No references for
    locations (they are the backdrop), just the Location.description."""
    results = []
    for lid, loc in locations.items():
        exists = loc.reference_path and os.path.exists(loc.reference_path)
        if exists and not force:
            print(f"  LOC   {lid:20} skip (exists)")
            results.append({"location_id": lid, "cached": True})
            continue
        prompt = (
            f"Location reference image. {loc.description} Manhwa / Korean "
            f"webtoon background art, cinematic composition, atmospheric. "
            f"No people in frame."
        )
        t0 = time.perf_counter()
        try:
            r = await generate_location_ref(lid, prompt, force=force)
            dt = time.perf_counter() - t0
            print(f"  LOC   {lid:20} OK  {dt:>5.1f}s  → {r['path']}")
            results.append(r)
        except Exception as e:
            print(f"  LOC   {lid:20} FAIL {type(e).__name__}: {str(e)[:140]}")
            results.append({"location_id": lid, "error": str(e)})
    return results


async def generate_panels(panels: list, force: bool) -> list[dict]:
    """Generate each panel via the manifest pipeline — refs are attached
    automatically and aspect ratio is enforced at the API layer."""
    results = []
    for p in panels:
        t0 = time.perf_counter()
        try:
            r = await generate_panel_from_manifest(p, force=force)
            dt = time.perf_counter() - t0
            cached = " (cached)" if r.get("cached") else ""
            print(f"  PANEL {p.id:30} OK  {dt:>5.1f}s  refs={r.get('references_used', 0)}{cached}")
            results.append(r)
        except Exception as e:
            print(f"  PANEL {p.id:30} FAIL {type(e).__name__}: {str(e)[:140]}")
            results.append({"panel_id": p.id, "error": str(e)})
    return results


async def main_async(story_id: str, refs_only: bool, panels_only: bool, force: bool) -> int:
    story = STORIES[story_id]
    print(f"\nStory: {story_id}")
    print(f"  characters: {len(story['characters'])}  locations: {len(story['locations'])}  panels: {len(story['panels'])}")

    if not panels_only:
        print("\n--- character refs ---")
        char_results = await ensure_character_refs(story["characters"], force=force)
        print("\n--- location refs ---")
        loc_results = await ensure_location_refs(story["locations"], force=force)
        char_fails = [r for r in char_results if "error" in r]
        loc_fails = [r for r in loc_results if "error" in r]
        if char_fails or loc_fails:
            print(f"\nABORT: {len(char_fails)} char + {len(loc_fails)} loc refs failed. "
                  f"Panels can't be generated without their anchors.")
            return 1

    if not refs_only:
        print("\n--- panels ---")
        panel_results = await generate_panels(story["panels"], force=force)
        panel_fails = [r for r in panel_results if "error" in r]
        panel_ok = len(panel_results) - len(panel_fails)
        print(f"\nPanels: {panel_ok}/{len(panel_results)} ok, {len(panel_fails)} failed")
        if panel_fails:
            return 1

    print("\nDone.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    ap.add_argument("story", choices=sorted(STORIES.keys()))
    ap.add_argument("--refs-only", action="store_true")
    ap.add_argument("--panels-only", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.refs_only and args.panels_only:
        print("--refs-only and --panels-only are mutually exclusive", file=sys.stderr)
        return 2
    return asyncio.run(main_async(args.story, args.refs_only, args.panels_only, args.force))


if __name__ == "__main__":
    sys.exit(main())
