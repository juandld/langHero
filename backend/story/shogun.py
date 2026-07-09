"""
SHOGUN STORY - Japan 1600, Sengoku Period

The player is a foreigner washed ashore, learning Japanese to survive.
Bimbo (AI companion) can freeze time to teach vocabulary.

Characters, locations, and panels are in shogun_data.py.
"""

import os
import asyncio
from story.manifest import get_panel_references
from story.skeleton import (
    StorySkeleton, Anchor, ChapterDef, BranchConfig, ReputationGateConfig,
    LearningObjective, StoryCategory,
)
from image.google import generate_character_ref, generate_location_ref
from story.shogun_data import (
    STORY_ID, STORY_TITLE, STORY_SUBTITLE,
    CHARACTERS, LOCATIONS, PANELS,
    IMAGE_CACHE_DIR, CHARACTER_REF_DIR, LOCATION_REF_DIR,
)


# ============================================================
# STORY SKELETON (extracted to shogun_skeleton.py)
# ============================================================

from story.shogun_skeleton import SHOGUN_SKELETON, STORY_SKELETONS, SHOGUN_CATEGORIES, SHOGUN_STYLE_TO_CATEGORY  # noqa: F401



def get_skeleton(story_id: str) -> "StorySkeleton | None":
    """Get a story skeleton by ID."""
    return STORY_SKELETONS.get(story_id)


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def check_missing():
    """Check which references need to be generated."""
    missing = {"characters": [], "locations": []}

    for char_id, char in CHARACTERS.items():
        if not char.reference_path or not os.path.exists(char.reference_path):
            missing["characters"].append(char_id)

    for loc_id, loc in LOCATIONS.items():
        if not loc.reference_path or not os.path.exists(loc.reference_path):
            missing["locations"].append(loc_id)

    return missing


def print_summary():
    """Print story summary."""
    print(f"\n{'='*50}")
    print(f"STORY: {STORY_TITLE}")
    print(f"ID: {STORY_ID}")
    print(f"{'='*50}")
    print(f"\nCharacters: {len(CHARACTERS)}")
    for cid, char in CHARACTERS.items():
        has_ref = "✓" if char.reference_path and os.path.exists(char.reference_path) else "✗"
        print(f"  [{has_ref}] {cid}: {char.name}")

    print(f"\nLocations: {len(LOCATIONS)}")
    for lid, loc in LOCATIONS.items():
        has_ref = "✓" if loc.reference_path and os.path.exists(loc.reference_path) else "✗"
        print(f"  [{has_ref}] {lid}: {loc.name}")

    print(f"\nPanels: {len(PANELS)}")
    chapters = {}
    for p in PANELS:
        chapters[p.chapter] = chapters.get(p.chapter, 0) + 1
    for ch, count in chapters.items():
        print(f"  {ch}: {count} panels")


async def generate_references(force=False):
    """Generate missing character and location references."""
    missing = check_missing()

    for char_id in missing["characters"]:
        char = CHARACTERS[char_id]
        prompt = f"""Manhwa/Korean webtoon style character portrait.

{char.description}

Portrait shot, shoulders up, facing camera.
Clean background. Professional character design reference quality.
Expressive manhwa style, clean linework, soft cel-shading.

NO TEXT IN IMAGE."""

        print(f"Generating character: {char_id}...")
        result = await generate_character_ref(char_id, prompt, force=force)
        print(f"  -> {result['path']}")

    for loc_id in missing["locations"]:
        loc = LOCATIONS[loc_id]
        prompt = f"""Manhwa/Korean webtoon style environment.

{loc.description}

Wide establishing shot. Rich detail.
Clean manhwa aesthetic, soft lighting.

NO TEXT IN IMAGE."""

        print(f"Generating location: {loc_id}...")
        result = await generate_location_ref(loc_id, prompt, force=force)
        print(f"  -> {result['path']}")


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    import sys
    from story.panels_test import generate_all_panels

    if len(sys.argv) < 2:
        print_summary()
        print("\nUsage:")
        print("  python -m story.shogun check    - Check missing references")
        print("  python -m story.shogun generate - Generate character/location refs")
        print("  python -m story.shogun panels   - Generate all panels")
        print("  python -m story.shogun all      - Generate everything")
        sys.exit(0)

    cmd = sys.argv[1]
    force = "--force" in sys.argv

    if cmd == "check":
        missing = check_missing()
        print("Missing references:")
        print(f"  Characters: {missing['characters']}")
        print(f"  Locations: {missing['locations']}")

    elif cmd == "generate":
        asyncio.run(generate_references(force))

    elif cmd == "panels":
        # Update the manifest with our data
        from story import manifest as story_manifest
        story_manifest.SHOGUN_CHARACTERS = CHARACTERS
        story_manifest.SHOGUN_LOCATIONS = LOCATIONS
        story_manifest.SHOGUN_PANELS = PANELS
        asyncio.run(generate_all_panels(force))

    elif cmd == "all":
        asyncio.run(generate_references(force))
        from story import manifest as story_manifest
        story_manifest.SHOGUN_CHARACTERS = CHARACTERS
        story_manifest.SHOGUN_LOCATIONS = LOCATIONS
        story_manifest.SHOGUN_PANELS = PANELS
        asyncio.run(generate_all_panels(force))

    else:
        print(f"Unknown command: {cmd}")
