#!/usr/bin/env python3
"""Generate Roberto's HUD portrait + optional Manuela/Bolivar refs.

Tries Google Gemini nano-banana first (per the manifest pipeline). If Gemini
returns 429 (free-tier quota exhausted — see MEMORY/reference_gemini_quota),
falls back to OpenAI gpt-image-1.5. Either way the file lands at
image_cache/characters/<id>.png which the backend already serves at
/images/generated/characters/<id>.png.

Usage:
  cd /home/nellie/workspace/heroes/langHero
  backend/venv/bin/python scripts/gen_roberto.py            # Roberto only
  backend/venv/bin/python scripts/gen_roberto.py --all      # + Manuela, Bolivar, sister
  backend/venv/bin/python scripts/gen_roberto.py --force    # regenerate even if cached
"""
import asyncio
import base64
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from story.manifest import MANUELA_CHARACTERS  # noqa: E402
from image.google import generate_character_ref  # noqa: E402

OUTPUT_DIR = ROOT / "image_cache" / "characters"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _hud_portrait_prompt(description: str) -> str:
    return (
        "Painterly manhwa portrait avatar for a game HUD. "
        "Head and chest only, framed tightly and centered, head not cut off at the crown. "
        f"{description} "
        "Rich dark painterly background, warm candle-light rim light, intentional HUD avatar framing."
    )


def _openai_fallback(char_id: str, description: str, force: bool) -> dict:
    out = OUTPUT_DIR / f"{char_id}.png"
    if out.exists() and not force:
        return {"character_id": char_id, "path": str(out), "cached": True}
    from openai import OpenAI
    client = OpenAI()
    r = client.images.generate(
        model="gpt-image-1.5",
        prompt=_hud_portrait_prompt(description),
        size="1024x1024",
        quality="medium",
        n=1,
    )
    d = r.data[0]
    data = base64.b64decode(d.b64_json) if getattr(d, "b64_json", None) else urllib.request.urlopen(d.url).read()
    out.write_bytes(data)
    return {"character_id": char_id, "path": str(out), "cached": False}


async def _generate_one(char_id: str, description: str, force: bool) -> dict:
    try:
        res = await generate_character_ref(
            character_id=char_id, prompt=description, face_reference=None, force=force
        )
        return res
    except Exception as e:
        msg = str(e)
        if "429" in msg or "quota" in msg.lower():
            print(f"    gemini quota exhausted, falling back to OpenAI")
            return _openai_fallback(char_id, description, force)
        raise


async def main() -> int:
    if not (os.getenv("GOOGLE_API_KEY") or os.getenv("OPENAI_API_KEY")):
        print("ERROR: neither GOOGLE_API_KEY nor OPENAI_API_KEY is set.", file=sys.stderr)
        return 2

    force = "--force" in sys.argv
    only_roberto = {"roberto": MANUELA_CHARACTERS["roberto"]}
    which = MANUELA_CHARACTERS if "--all" in sys.argv else only_roberto

    print(f"Generating {len(which)} character ref(s): {', '.join(which)}  force={force}")
    for cid, char in which.items():
        print(f"  → {cid} …", flush=True)
        try:
            res = await _generate_one(cid, char.description, force)
            print(f"    {'cached' if res.get('cached') else 'generated'} → {res.get('path')}")
        except Exception as e:
            print(f"    FAILED: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
