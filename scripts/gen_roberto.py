#!/usr/bin/env python3
"""One-shot generator for Roberto's HUD portrait + base character refs for Manuela.

Requires GOOGLE_API_KEY in the environment with Gemini nano-banana access.
Writes PNGs to backend/image_cache/characters/.

Usage:
  cd /home/nellie/workspace/heroes/langHero
  GOOGLE_API_KEY=xxx backend/venv/bin/python scripts/gen_roberto.py            # Roberto only
  GOOGLE_API_KEY=xxx backend/venv/bin/python scripts/gen_roberto.py --all      # Roberto + Manuela + Bolívar + sister
  GOOGLE_API_KEY=xxx backend/venv/bin/python scripts/gen_roberto.py --force    # re-generate even if cached
"""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from story.manifest import MANUELA_CHARACTERS  # noqa: E402
from image.google import generate_character_ref  # noqa: E402


ONLY_ROBERTO = {k: v for k, v in MANUELA_CHARACTERS.items() if k == "roberto"}


async def main() -> int:
    if not os.getenv("GOOGLE_API_KEY"):
        print(
            "ERROR: GOOGLE_API_KEY not set. The manifest system uses Gemini nano-banana.\n"
            "Set it (and make sure billing is enabled on the GCP project per MEMORY.md).",
            file=sys.stderr,
        )
        return 2

    force = "--force" in sys.argv
    which = MANUELA_CHARACTERS if "--all" in sys.argv else ONLY_ROBERTO
    print(f"Generating {len(which)} character ref(s): {', '.join(which)}  force={force}")

    for cid, char in which.items():
        print(f"  → {cid} …", flush=True)
        try:
            res = await generate_character_ref(
                character_id=cid,
                prompt=char.description,
                face_reference=None,
                force=force,
            )
            print(f"    {'cached' if res.get('cached') else 'generated'} → {res.get('path')}")
        except Exception as e:
            print(f"    FAILED: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
