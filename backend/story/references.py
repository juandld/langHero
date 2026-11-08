"""Reference-image bookkeeping shared by every story module.

Story modules (shogun.py, template.py and the stories copied from it) only
define CHARACTERS / LOCATIONS / PANELS; checking, summarising and generating
the character + location reference images lives here once. Works with any
character/location object that has .name, .description and .reference_path.
"""
import os

from image.google import generate_character_ref, generate_location_ref


def _has_ref(item) -> bool:
    return bool(item.reference_path and os.path.exists(item.reference_path))


def check_missing(characters: dict, locations: dict) -> dict:
    """Which references still need to be generated."""
    return {
        "characters": [cid for cid, c in characters.items() if not _has_ref(c)],
        "locations": [lid for lid, loc in locations.items() if not _has_ref(loc)],
    }


def print_summary(title: str, story_id: str, characters: dict, locations: dict, panels: list) -> None:
    print(f"\n{'='*50}")
    print(f"STORY: {title}")
    print(f"ID: {story_id}")
    print(f"{'='*50}")
    print(f"\nCharacters: {len(characters)}")
    for cid, char in characters.items():
        print(f"  [{'✓' if _has_ref(char) else '✗'}] {cid}: {char.name}")
    print(f"\nLocations: {len(locations)}")
    for lid, loc in locations.items():
        print(f"  [{'✓' if _has_ref(loc) else '✗'}] {lid}: {loc.name}")
    print(f"\nPanels: {len(panels)}")
    chapters: dict = {}
    for p in panels:
        chapters[p.chapter] = chapters.get(p.chapter, 0) + 1
    for ch, count in chapters.items():
        print(f"  {ch}: {count} panels")


async def generate_references(characters: dict, locations: dict, force=False) -> None:
    """Generate missing character and location references."""
    missing = check_missing(characters, locations)
    for char_id in missing["characters"]:
        prompt = f"""Manhwa/Korean webtoon style character portrait.

{characters[char_id].description}

Portrait shot, shoulders up, facing camera.
Clean background. Professional character design reference quality.
Expressive manhwa style, clean linework, soft cel-shading.

NO TEXT IN IMAGE."""
        print(f"Generating character: {char_id}...")
        result = await generate_character_ref(char_id, prompt, force=force)
        print(f"  -> {result['path']}")
    for loc_id in missing["locations"]:
        prompt = f"""Manhwa/Korean webtoon style environment.

{locations[loc_id].description}

Wide establishing shot. Rich detail.
Clean manhwa aesthetic, soft lighting.

NO TEXT IN IMAGE."""
        print(f"Generating location: {loc_id}...")
        result = await generate_location_ref(loc_id, prompt, force=force)
        print(f"  -> {result['path']}")
