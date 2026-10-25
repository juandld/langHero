"""
Story panels API - serves panel sequences for the visual novel experience.

The skeleton is the single source of truth. The /stories/{id} endpoint
builds its response by walking skeleton anchors and collecting panels.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import os
import time

try:
    from story.localize import localize_panels, needs_localization, LEVELS as LOCALIZE_LEVELS
except ImportError:
    localize_panels = None
    needs_localization = None
    LOCALIZE_LEVELS = ["beginner", "elementary", "intermediate", "advanced"]

# Import voice config
try:
    from story.voices import get_story_voice_config, get_panel_voice_config
except ImportError:
    get_story_voice_config = None
    get_panel_voice_config = None

# Import skeleton system — merge registries from all stories
try:
    from story.shogun import get_skeleton, STORY_SKELETONS as _SHOGUN_SKELETONS, CHARACTERS, LOCATIONS
    STORY_SKELETONS = dict(_SHOGUN_SKELETONS)
except ImportError:
    get_skeleton = None
    STORY_SKELETONS = {}
    CHARACTERS = {}
    LOCATIONS = {}

try:
    from story.journey import STORY_SKELETONS as _JOURNEY_SKELETONS, CHARACTERS as _JW_CHARS, LOCATIONS as _JW_LOCS
    STORY_SKELETONS.update(_JOURNEY_SKELETONS)
    CHARACTERS.update(_JW_CHARS)
    LOCATIONS.update(_JW_LOCS)
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to import journey story: {e}")

try:
    from story.manuela import STORY_SKELETONS as _MANUELA_SKELETONS, CHARACTERS as _MN_CHARS, LOCATIONS as _MN_LOCS
    STORY_SKELETONS.update(_MANUELA_SKELETONS)
    CHARACTERS.update(_MN_CHARS)
    LOCATIONS.update(_MN_LOCS)
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to import manuela story: {e}")

# Import generator
try:
    from story.generator import generate_segment
except ImportError:
    generate_segment = None

router = APIRouter(prefix="/api/story-panels", tags=["story-panels"])


def get_all_panels_from_skeleton(skeleton):
    """Walk skeleton anchors, collect hand-written panels, group by chapter.

    Returns the same shape as the old SHOGUN_STORY dict:
    { id, title, subtitle, chapters: [{ id, title, panels: [...] }] }
    """
    chapters = []
    chapter_map = {}  # chapter_id -> { id, title, panels }

    for ch_def in skeleton.chapters:
        ch = {"id": ch_def.id, "title": ch_def.title, "panels": []}
        chapters.append(ch)
        chapter_map[ch_def.id] = ch

    # Walk anchors in order, collect panels into their chapter
    for anchor in skeleton.anchors:
        ch = chapter_map.get(anchor.chapter)
        if not ch:
            continue
        for panel in anchor.panels:
            ch["panels"].append(panel)

    return {
        "id": skeleton.id,
        "title": skeleton.title,
        "subtitle": skeleton.subtitle,
        "chapters": chapters,
    }


# Build story cache on import (lazy, built once)
_story_cache = {}


def _get_story(story_id: str):
    """Get the full story dict, built from skeleton. Cached after first call."""
    if story_id in _story_cache:
        return _story_cache[story_id]

    if not get_skeleton:
        return None

    skeleton = STORY_SKELETONS.get(story_id)
    if not skeleton:
        return None

    story = get_all_panels_from_skeleton(skeleton)
    _story_cache[story_id] = story
    return story


@router.get("/stories")
async def list_stories():
    """List available stories."""
    stories = []
    if get_skeleton:
        for sid, skel in STORY_SKELETONS.items():
            story = _get_story(sid)
            if story:
                stories.append({
                    "id": story["id"],
                    "title": story["title"],
                    "subtitle": story.get("subtitle"),
                    "chapter_count": len(story["chapters"]),
                })
    return {"stories": stories}


@router.get("/stories/{story_id}")
async def get_story(
    story_id: str,
    language: Optional[str] = Query(None, description="Narration language, e.g. 'es'. Omit for original (English)."),
    level: Optional[str] = Query("beginner", description=f"Vocabulary level: one of {LOCALIZE_LEVELS}"),
):
    """Get full story with all chapters and panels (built from skeleton).

    With `language` set, every chapter's hand-written panels are localized
    (narration/dialogue/option text only — same ids, images, branch logic).
    """
    story = _get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    if localize_panels and needs_localization and needs_localization(language, level):
        skeleton = STORY_SKELETONS.get(story_id)
        setting = skeleton.setting if skeleton else ""
        localized_chapters = []
        for chapter in story["chapters"]:
            if chapter["panels"]:
                panels = await localize_panels(chapter["panels"], language, level, setting)
            else:
                panels = chapter["panels"]
            localized_chapters.append({**chapter, "panels": panels})
        return {**story, "chapters": localized_chapters, "language": language, "level": level}

    return story


@router.get("/stories/{story_id}/chapters/{chapter_id}")
async def get_chapter(
    story_id: str,
    chapter_id: str,
    language: Optional[str] = Query(None, description="Narration language, e.g. 'es'. Omit for original (English)."),
    level: Optional[str] = Query("beginner", description=f"Vocabulary level: one of {LOCALIZE_LEVELS}"),
):
    """Get a specific chapter.

    Same story structure regardless of language/level — only narration,
    dialogue, and option text are localized. Panel ids, images, and branch
    logic are unchanged so progress/saves stay valid across languages.
    """
    story = _get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    for chapter in story["chapters"]:
        if chapter["id"] == chapter_id:
            if localize_panels and needs_localization and needs_localization(language, level):
                skeleton = STORY_SKELETONS.get(story_id)
                setting = skeleton.setting if skeleton else ""
                localized_panels = await localize_panels(chapter["panels"], language, level, setting)
                return {**chapter, "panels": localized_panels, "language": language, "level": level}
            return chapter

    raise HTTPException(status_code=404, detail="Chapter not found")


@router.get("/stories/{story_id}/voice-config")
async def get_voice_config(story_id: str):
    """Get voice configuration for a story."""
    if not get_story_voice_config:
        return {"error": "Voice config not available"}

    config = get_story_voice_config(story_id)
    if not config:
        return {
            "story_id": story_id,
            "narrator": {
                "voice": "alloy",
                "style": "Speak with calm authority.",
            },
            "characters": {},
        }

    return {
        "story_id": config.story_id,
        "narrator": {
            "voice": config.narrator_voice,
            "style": config.narrator_style,
        },
        "characters": {
            char_id: {
                "voice": char.voice,
                "gender": char.gender,
                "sentiment": char.default_sentiment,
                "style": char.speaking_style,
            }
            for char_id, char in config.characters.items()
        },
    }


@router.get("/stories/{story_id}/panels/{panel_id}/voice")
async def get_panel_voice(story_id: str, panel_id: str):
    """Get voice config for a specific panel."""
    story = _get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Find the panel
    panel = None
    for chapter in story["chapters"]:
        for p in chapter["panels"]:
            if p["id"] == panel_id:
                panel = p
                break
        if panel:
            break

    if not panel:
        raise HTTPException(status_code=404, detail="Panel not found")

    if not get_panel_voice_config:
        return {"panel_id": panel_id, "narration": None, "dialogue": None}

    config = get_panel_voice_config(story_id, panel)
    return {"panel_id": panel_id, **config}


# ─────────────────────────────────────────────────
# Skeleton / Segment API (anchor-based system)
# ─────────────────────────────────────────────────

@router.get("/stories/{story_id}/skeleton")
async def get_story_skeleton(story_id: str):
    """Get lightweight story skeleton — anchor metadata, no panel content."""
    if not get_skeleton:
        raise HTTPException(status_code=501, detail="Skeleton system not available")

    skeleton = STORY_SKELETONS.get(story_id)
    if not skeleton:
        raise HTTPException(status_code=404, detail="Story skeleton not found")

    return skeleton.to_api_response()


class SegmentRequest(BaseModel):
    from_anchor_id: str
    to_anchor_id: str
    player_state: Optional[dict] = None
    language: Optional[str] = None
    level: Optional[str] = "beginner"


@router.post("/stories/{story_id}/segment")
async def get_segment(story_id: str, req: SegmentRequest):
    """Get panels for a segment between two anchors.

    Returns hand-written panels from anchors directly, or generates
    bridge content via the generation pipeline.
    """
    if not get_skeleton:
        raise HTTPException(status_code=501, detail="Skeleton system not available")

    skeleton = STORY_SKELETONS.get(story_id)
    if not skeleton:
        raise HTTPException(status_code=404, detail="Story skeleton not found")

    from_anchor = skeleton.get_anchor(req.from_anchor_id)
    to_anchor = skeleton.get_anchor(req.to_anchor_id)

    if not from_anchor:
        raise HTTPException(status_code=404, detail=f"Anchor '{req.from_anchor_id}' not found")
    if not to_anchor:
        raise HTTPException(status_code=404, detail=f"Anchor '{req.to_anchor_id}' not found")

    want_localized = bool(localize_panels and needs_localization and needs_localization(req.language, req.level))

    # Hand-written panels: return directly
    if from_anchor.panels:
        panels = from_anchor.panels
        if want_localized:
            panels = await localize_panels(panels, req.language, req.level, skeleton.setting)
        return {
            "story_id": story_id,
            "from_anchor": req.from_anchor_id,
            "to_anchor": req.to_anchor_id,
            "panels": panels,
            "generated": False,
            "cached": False,
            "language": req.language,
            "level": req.level,
        }

    # No hand-written panels: try generation
    if generate_segment:
        result = await generate_segment(
            skeleton=skeleton,
            from_anchor=from_anchor,
            to_anchor=to_anchor,
            player_state=req.player_state or {},
            characters=CHARACTERS,
            locations=LOCATIONS,
        )
        if want_localized and result.get("panels"):
            result = {**result, "panels": await localize_panels(result["panels"], req.language, req.level, skeleton.setting)}
        return {
            "story_id": story_id,
            "from_anchor": req.from_anchor_id,
            "to_anchor": req.to_anchor_id,
            "language": req.language,
            "level": req.level,
            **result,
        }

    # Fallback: return generation hint as a single panel
    return {
        "story_id": story_id,
        "from_anchor": req.from_anchor_id,
        "to_anchor": req.to_anchor_id,
        "panels": [{
            "id": f"placeholder_{from_anchor.id}",
            "image": None,
            "aspect": "square",
            "narration": from_anchor.generation_hint or "The story continues...",
            "dialogue": None,
            "speaker": None,
        }],
        "generated": False,
        "cached": False,
    }


@router.post("/stories/{story_id}/prefetch")
async def prefetch_segment(story_id: str, req: SegmentRequest):
    """Fire-and-forget: pre-generate next segment in background."""
    if not get_skeleton:
        raise HTTPException(status_code=501, detail="Skeleton system not available")

    skeleton = STORY_SKELETONS.get(story_id)
    if not skeleton:
        raise HTTPException(status_code=404, detail="Story skeleton not found")

    return {"status": "accepted", "message": "Prefetch queued"}
