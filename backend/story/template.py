"""
STORY TEMPLATE - Copy this file to create a new story.

Rename to: story_{story_id}.py (e.g., story_heian.py, story_meiji.py)

WORKFLOW:
1. Copy this template
2. Define your characters (with detailed visual descriptions)
3. Define your locations
4. Define your panels (tracking which characters appear)
5. Run: python story_{id}.py check    -> See missing references
6. Run: python story_{id}.py generate -> Generate character/location refs
7. Run: python story_{id}.py panels   -> Generate all story panels
8. Add story to routes/story_panels.py
"""

import os
import asyncio
from dataclasses import dataclass, field
from typing import Optional

# Import from the core system
from story.manifest import Character, Location, PanelSpec, get_panel_references
from story.panels_test import build_manifest_prompt, generate_panel_from_manifest
from story import references

# Paths
IMAGE_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "image_cache")
CHARACTER_REF_DIR = os.path.join(IMAGE_CACHE_DIR, "characters")
LOCATION_REF_DIR = os.path.join(IMAGE_CACHE_DIR, "locations")
PANEL_DIR = os.path.join(IMAGE_CACHE_DIR, "panels")


# ============================================================
# STORY METADATA
# ============================================================

STORY_ID = "template"  # Change this! Used for panel folders
STORY_TITLE = "Story Title"
STORY_SUBTITLE = "Setting and Era"


# ============================================================
# CHARACTERS
# ============================================================
#
# For each character that appears in your story:
# 1. Give them a unique ID (snake_case)
# 2. Write a DETAILED visual description (this goes in every prompt)
# 3. The system will generate a reference image
#
# Tips for good descriptions:
# - Age, build, distinguishing features
# - Hair style and color
# - Clothing (be period-specific)
# - Expression/demeanor
# - What makes them visually unique
#
# ============================================================

CHARACTERS = {
    # Example main character
    "protagonist_companion": Character(
        id="protagonist_companion",
        name="Character Name",
        description="""Detailed visual description here.
Age, build, face shape. Hair color and style.
Clothing with period-accurate details.
Expression and demeanor. Distinguishing features.
What makes them recognizable across panels.""",
        reference_path=os.path.join(CHARACTER_REF_DIR, "protagonist_companion.png"),
    ),

    # Example recurring side character
    "village_elder": Character(
        id="village_elder",
        name="Elder",
        description="""Detailed visual description here.""",
        reference_path=os.path.join(CHARACTER_REF_DIR, "village_elder.png"),
    ),

    # You can reuse characters from other stories by importing them:
    # from story_shogun import SHOGUN_CHARACTERS
    # "bimbo": SHOGUN_CHARACTERS["bimbo"],  # Reuse Bimbo
}


# ============================================================
# LOCATIONS
# ============================================================
#
# For each distinct location/setting:
# 1. Give it a unique ID
# 2. Describe the environment in detail
# 3. The system will generate a reference image
#
# ============================================================

LOCATIONS = {
    "main_location": Location(
        id="main_location",
        name="Location Name",
        description="""Detailed environment description.
Architecture, lighting, atmosphere.
Time of day, weather, mood.
Key visual elements that define this place.""",
        reference_path=os.path.join(LOCATION_REF_DIR, "main_location.png"),
    ),
}


# ============================================================
# PANELS
# ============================================================
#
# Each panel needs:
# - id: Unique identifier (used for filename)
# - chapter: Chapter folder name
# - panel_type: establishing|pov|dialogue|action|time_freeze|emotional
# - description: What happens in this panel (POV perspective!)
# - characters: List of character IDs that appear
# - location: Location ID for background
# - mood: Emotional tone (used for interpretation)
#
# IMPORTANT:
# - Always write from POV perspective (never show the player)
# - List ALL characters visible in the panel
# - Be specific about positioning and focus
#
# ============================================================

PANELS = [
    PanelSpec(
        id="ch01_01_opening",
        chapter="ch01",
        panel_type="establishing",
        description="""POV description of what the player sees.
Be specific about composition, who is where, what's happening.""",
        characters=[],  # List character IDs that appear
        location="main_location",
        mood="contemplative",
    ),

    PanelSpec(
        id="ch01_02_dialogue",
        chapter="ch01",
        panel_type="dialogue",
        description="""POV looking at character speaking.
They face the viewer directly. Describe their expression.""",
        characters=["protagonist_companion"],
        location="main_location",
        speaker="protagonist_companion",
        mood="warm",
    ),

    # Add more panels...
]


# ============================================================
# GENERATION FUNCTIONS
# ============================================================

async def generate_panels(force=False):
    """Generate all story panels."""

    results = []

    for panel in PANELS:
        refs = get_panel_references(panel, CHARACTERS, LOCATIONS)
        print(f"Generating {panel.id}...")
        print(f"  Characters: {panel.characters}")
        print(f"  References: {len(refs)} images")

        try:
            result = await generate_panel_from_manifest(panel, force)
            results.append(result)
            print(f"  -> {result['path']}")
        except Exception as e:
            print(f"  -> ERROR: {e}")
            results.append({"panel_id": panel.id, "error": str(e)})

    return results



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

    if len(sys.argv) < 2:
        print_summary()
        print("\nUsage:")
        print("  python -m story.template check    - Check missing references")
        print("  python -m story.template generate - Generate character/location refs")
        print("  python -m story.template panels   - Generate all panels")
        print("  python -m story.template all      - Generate everything")
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
        asyncio.run(generate_panels(force))

    elif cmd == "all":
        asyncio.run(generate_references(force))
        asyncio.run(generate_panels(force))

    else:
        print(f"Unknown command: {cmd}")
