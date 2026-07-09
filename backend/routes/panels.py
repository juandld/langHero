"""
Visual panels API endpoints for manga/webtoon style panels.
"""

import os
import json as json_mod
import asyncio
from fastapi import APIRouter, Request, HTTPException
from story import to_panels as story_to_panels
from image.visual_styles import ArtStyle, Panel, PanelType, Mood, VisualEffect, get_intro_panels
from services.scenarios import get_scenario_by_id
from image import dalle as image_gen
from security import parse_json_body

router = APIRouter(prefix="/api/panels", tags=["panels"])

_STORIES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "stories.json")


def _load_stories_data() -> dict:
    """Load and return stories.json, raising HTTPException on failure."""
    try:
        with open(_STORIES_PATH, "r") as f:
            return json_mod.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load stories: {e}")


def _find_story(stories_data: dict, story_id: str) -> dict:
    """Find a story by ID in stories data, raising 404 if not found."""
    for s in stories_data.get("stories", []):
        if s.get("id") == story_id:
            return s
    raise HTTPException(status_code=404, detail="story_not_found")


def _parse_art_style(style_str: str, default: ArtStyle = ArtStyle.MANHWA) -> ArtStyle:
    """Parse an art style string, returning default on invalid values."""
    try:
        return ArtStyle(style_str.lower())
    except ValueError:
        return default


def _lookup_panel(panels_db: dict, panel_id: str) -> dict:
    """Look up a panel by ID across all categories in the panels database."""
    for cat, cat_panels in panels_db.items():
        if panel_id in cat_panels:
            panel_data = cat_panels[panel_id]
            return {
                "id": panel_data.get("id", panel_id),
                "category": cat,
                "scene_description": panel_data.get("scene_description", ""),
                "mood": panel_data.get("mood", "warm"),
                "effects": panel_data.get("effects", []),
                "art_style": panel_data.get("art_style", "manhwa"),
                "image_url": panel_data.get("image_url"),
            }
    return {
        "id": panel_id,
        "category": "unknown",
        "scene_description": f"Panel {panel_id}",
        "mood": "warm",
        "effects": [],
        "art_style": "manhwa",
        "image_url": None,
    }


def _resolve_panel_assignments(assigned) -> dict:
    """Convert any panel assignment format (dict, list, str) to line-indexed dict."""
    if isinstance(assigned, dict):
        return assigned
    if isinstance(assigned, list):
        return {str(idx): pid for idx, pid in enumerate(assigned)}
    if isinstance(assigned, str):
        return {"0": assigned}
    raise HTTPException(status_code=500, detail="invalid_panel_assignment_format")


@router.post("/from-story")
async def api_story_to_panels(request: Request):
    """Convert narrative text into visual panel sequence.

    Body: {
        "narrative": "Story text...",
        "title": "Scene Title",
        "art_style": "manhwa",  # manhwa, manga, ghibli, dramatic, minimal
        "max_panels": 12,
        "target_language": "Japanese"
    }

    Returns: {sequence with panels}
    """
    body = await parse_json_body(request)

    narrative = str((body or {}).get("narrative", "")).strip()
    if not narrative:
        raise HTTPException(status_code=400, detail="narrative_required")

    title = str((body or {}).get("title", "Scene")).strip()
    max_panels = int((body or {}).get("max_panels", 12))
    target_language = str((body or {}).get("target_language", "Japanese")).strip()
    art_style = _parse_art_style(str((body or {}).get("art_style", "manhwa")))

    try:
        sequence = await asyncio.to_thread(
            story_to_panels.adapt_story_to_panels,
            narrative,
            title=title,
            art_style=art_style,
            target_language=target_language,
            max_panels=max_panels,
        )
        return story_to_panels.sequence_to_dict(sequence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-scenario/{scenario_id}")
async def api_scenario_to_panels(scenario_id: int, request: Request):
    """Convert a scenario into visual panels.

    Returns: {sequence with panels}
    """
    scenario = get_scenario_by_id(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="scenario_not_found")

    body = await parse_json_body(request)
    art_style = _parse_art_style(str((body or {}).get("art_style", "manhwa")))

    try:
        sequence = await asyncio.to_thread(
            story_to_panels.adapt_scenario_to_panels,
            scenario,
            art_style=art_style,
        )
        return story_to_panels.sequence_to_dict(sequence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-images")
async def api_generate_panel_images(request: Request):
    """Generate images for a panel sequence.

    Body: {
        "panels": [...],  # Array of panel objects
        "context": "Story context",
        "force": false
    }

    Returns: {results: [{url, panel_id, cached, error?}]}
    """
    body = await parse_json_body(request)

    panels_data = (body or {}).get("panels", [])
    context = str((body or {}).get("context", "")).strip()
    force = bool((body or {}).get("force", False))

    if not panels_data:
        raise HTTPException(status_code=400, detail="panels_required")

    # Convert dict panels to Panel objects
    panels = []
    for p in panels_data:
        try:
            panel_type = PanelType(p.get("type", "full"))
        except ValueError:
            panel_type = PanelType.FULL

        art_style = _parse_art_style(p.get("art_style", "manhwa"))

        try:
            mood = Mood(p.get("mood", "warm"))
        except ValueError:
            mood = Mood.WARM

        effects = []
        for e in p.get("effects", []):
            try:
                effects.append(VisualEffect(e))
            except ValueError:
                pass

        panels.append(Panel(
            id=p.get("id", f"panel_{len(panels)}"),
            type=panel_type,
            scene_description=p.get("scene_description", ""),
            art_style=art_style,
            mood=mood,
            effects=effects,
            character_expression=p.get("character_expression"),
            image_url=p.get("image_url"),
        ))

    results = []
    for panel in panels:
        try:
            result = await asyncio.to_thread(
                image_gen.generate_panel_image,
                panel,
                context,
                force,
            )
            results.append(result)
        except Exception as e:
            results.append({
                "url": None,
                "panel_id": panel.id,
                "error": str(e),
            })

    return {"results": results}


@router.get("/lookup/{panel_id}")
async def api_get_panel_by_id(panel_id: str):
    """Get a panel definition by its ID.

    Searches through all panel categories (holographic, cinematic, tutorial).

    Returns: {panel data} or 404
    """
    stories_data = _load_stories_data()
    panels_db = stories_data.get("panels", {})
    result = _lookup_panel(panels_db, panel_id)

    if result["category"] == "unknown":
        raise HTTPException(status_code=404, detail="panel_not_found")
    return result


@router.get("/sequence/{dialogue_key}")
async def api_get_panel_sequence(dialogue_key: str, story_id: str = "shogun"):
    """Get the panel sequence for a dialogue.

    Returns line-indexed panel definitions for the given dialogue key.
    Each dialogue line index maps to its corresponding panel.

    Returns: {panels: {"0": {...}, "1": {...}, ...}, dialogue_key, story_id}
    """
    stories_data = _load_stories_data()
    story = _find_story(stories_data, story_id)

    panel_assignments = story.get("panel_assignments", {})
    assigned = panel_assignments.get(dialogue_key)

    if not assigned:
        raise HTTPException(status_code=404, detail="no_panels_assigned")

    panels_db = stories_data.get("panels", {})
    indexed = _resolve_panel_assignments(assigned)
    result_panels = {idx: _lookup_panel(panels_db, pid) for idx, pid in indexed.items()}

    return {
        "story_id": story_id,
        "dialogue_key": dialogue_key,
        "panels": result_panels,
    }


@router.get("/intro")
async def api_get_intro_panels():
    """Get the pre-defined intro panel sequence.

    Returns: {panels: [...]}
    """
    panels = get_intro_panels()

    # Check for cached images for each panel
    result_panels = []
    for p in panels:
        panel_data = {
            "id": p.id,
            "type": p.type.value,
            "scene_description": p.scene_description,
            "mood": p.mood.value,
            "art_style": p.art_style.value,
            "effects": [e.value for e in p.effects],
            "character_expression": p.character_expression,
            "duration_ms": p.duration_ms,
        }

        # Check if image is cached, otherwise use fallback URL
        cache_key = image_gen._cache_key_for_panel(
            p.id, p.scene_description, p.art_style.value
        )
        cache_path = os.path.join(image_gen.IMAGE_CACHE_DIR, f"{cache_key}.png")
        if os.path.exists(cache_path):
            panel_data["image_url"] = f"/images/generated/{cache_key}.png"
        elif p.image_url:
            panel_data["image_url"] = p.image_url

        result_panels.append(panel_data)

    return {"panels": result_panels}


@router.post("/from-dialogue/{story_id}/{dialogue_key}")
async def api_dialogue_to_panels(story_id: str, dialogue_key: str, request: Request):
    """Generate panels from a story dialogue sequence.

    Uses LLM to analyze dialogue content and create appropriate
    visual panel descriptions for each narrative beat.

    Body: {
        "story_context": "Optional additional context",
        "art_style": "manhwa"  # optional override
    }

    Returns: {sequence with panels}
    """
    stories_data = _load_stories_data()
    story = _find_story(stories_data, story_id)

    # Get the dialogue
    dialogue_lines = stories_data.get("dialogues", {}).get(dialogue_key)
    if not dialogue_lines:
        raise HTTPException(status_code=404, detail="dialogue_not_found")

    # Get existing panels for reference
    existing_panels = stories_data.get("panels", {}).get(story_id, {})

    # Determine aesthetic from story structure
    aesthetic = "holographic"
    if dialogue_key in ["awakening", "first_success", "time_freeze_lesson"]:
        aesthetic = story.get("main", {}).get("aesthetic", "cinematic")
    elif dialogue_key in ["tutorial_intro", "tutorial_to_story"]:
        aesthetic = story.get("tutorial", {}).get("aesthetic", "holographic")
    elif dialogue_key.startswith("shogun"):
        aesthetic = "holographic"  # Briefing still in simulation

    # Parse request body
    body = await parse_json_body(request)

    story_context = str((body or {}).get("story_context", story.get("description", ""))).strip()

    # Art style override
    style_str = str((body or {}).get("art_style", "")).lower()
    if style_str:
        try:
            # Override aesthetic based on art style
            if style_str in ["dramatic"]:
                aesthetic = "cinematic"
        except Exception:
            pass

    try:
        sequence = await asyncio.to_thread(
            story_to_panels.adapt_dialogue_to_panels,
            dialogue_key,
            dialogue_lines,
            story_context=story_context,
            aesthetic=aesthetic,
            existing_panels=existing_panels,
        )
        return story_to_panels.sequence_to_dict(sequence)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/story/{story_id}/all-dialogues")
async def api_generate_all_story_panels(story_id: str):
    """Get panel requirements for all dialogues in a story.

    Returns a summary of which dialogues need panels and their current status.

    Returns: {
        "story_id": "shogun",
        "dialogues": [
            {
                "key": "tutorial_intro",
                "line_count": 7,
                "aesthetic": "holographic",
                "has_assignment": true,
                "assigned_panels": ["future_ship"]
            },
            ...
        ]
    }
    """
    stories_data = _load_stories_data()
    story = _find_story(stories_data, story_id)

    # Get all dialogues referenced by this story
    tutorial = story.get("tutorial", {})
    main = story.get("main", {})
    panel_assignments = story.get("panel_assignments", {})

    # Collect all dialogue keys
    dialogue_keys = set()
    for key in [
        tutorial.get("intro_dialogue"),
        tutorial.get("transition_dialogue"),
        main.get("intro_dialogue"),
        main.get("drop_sequence"),
        main.get("awakening_dialogue"),
        main.get("time_freeze_lesson"),
        main.get("first_success"),
    ]:
        if key:
            dialogue_keys.add(key)

    all_dialogues = stories_data.get("dialogues", {})
    result = []

    for key in sorted(dialogue_keys):
        lines = all_dialogues.get(key, [])
        assignment = panel_assignments.get(key)

        # Determine aesthetic
        if key in [tutorial.get("intro_dialogue"), tutorial.get("transition_dialogue")]:
            aesthetic = tutorial.get("aesthetic", "holographic")
        else:
            aesthetic = main.get("aesthetic", "cinematic")

        assigned_panels = list(_resolve_panel_assignments(assignment).values()) if assignment else []

        result.append({
            "key": key,
            "line_count": len(lines),
            "aesthetic": aesthetic,
            "has_assignment": assignment is not None,
            "assigned_panels": assigned_panels,
            "panel_count": len(assigned_panels),
            "has_1to1_mapping": len(assigned_panels) == len(lines),
            "speakers": list(set(line.get("speaker", "unknown") for line in lines)),
        })

    return {
        "story_id": story_id,
        "dialogues": result,
    }
