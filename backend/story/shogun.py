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
from story import references
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
    return references.check_missing(CHARACTERS, LOCATIONS)


def print_summary():
    references.print_summary(STORY_TITLE, STORY_ID, CHARACTERS, LOCATIONS, PANELS)


async def generate_references(force=False):
    await references.generate_references(CHARACTERS, LOCATIONS, force=force)

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
