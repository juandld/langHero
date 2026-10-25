"""One-off: generate the 'bimbo' companion character reference portrait.

David wants the AI companion depicted as a handsome human ("Roberto") instead
of showing nothing (the panel fell back to a plain gradient — no reference
image existed on disk at image_cache/characters/bimbo.png). Uses the existing
Nano Banana pipeline so the result matches the rest of the game's manhwa art.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from image.google import generate_character_ref

PROMPT = """Create a single character reference portrait, close-up, 1:1 aspect ratio.
Korean manhwa/webtoon aesthetic. Clean linework with confident strokes, cel-shaded coloring.
Subject: Roberto, a warm and handsome young man in his late twenties, an AI holographic
companion who guides and teaches the player. Friendly confident smile, kind intelligent eyes,
short dark hair. Futuristic holographic effects: soft purple-to-cyan gradient glow outlining
his silhouette, faint floating light particles around him. Clean sci-fi aesthetic mixed with
manhwa style. Neutral dark background so the character reads clearly. No text, no logos."""


async def main():
    result = await generate_character_ref("bimbo", PROMPT, force=True)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
