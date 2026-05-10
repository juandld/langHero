"""
Segment Generator — AI generates bridge panels between story anchors.

Uses GPT-4o for literary quality. Generated panels use the exact same
format as hand-written ones so the frontend doesn't know the difference.
"""

import json
import logging
import os
from typing import Optional

import config
from story.skeleton import StorySkeleton, Anchor
from story.segment_cache import compute_state_hash, get_cached, set_cached

logger = logging.getLogger(__name__)

IMAGE_BASE_URL = "/images/generated"


def _build_generation_prompt(
    skeleton: StorySkeleton,
    from_anchor: Anchor,
    to_anchor: Anchor,
    player_state: dict,
    characters: dict,
    locations: dict,
) -> str:
    """Build the LLM prompt for generating bridge panels."""

    reputation = player_state.get("reputation", {})
    dominant = "pragmatic"
    if reputation:
        dominant = max(reputation, key=lambda k: reputation.get(k, 0))

    recent_choices = player_state.get("branch_history", [])[-3:]

    # Character descriptions for characters in the anchors
    char_ids = set(from_anchor.characters + to_anchor.characters)
    char_descriptions = []
    for cid in char_ids:
        char = characters.get(cid)
        if char:
            char_descriptions.append(f"- {char.name}: {char.description}")

    # Location descriptions
    loc_descriptions = []
    for lid in [from_anchor.location, to_anchor.location]:
        if lid:
            loc = locations.get(lid)
            if loc:
                loc_descriptions.append(f"- {loc.name}: {loc.description}")

    # Learning objectives
    learning_text = ""
    if to_anchor.learning:
        lo = to_anchor.learning
        learning_text = f"""
Learning objectives for the next scene:
- Vocabulary: {', '.join(lo.vocabulary)}
- Grammar: {', '.join(lo.grammar)}
- Cultural: {', '.join(lo.cultural)}
- Difficulty: {lo.difficulty}
"""

    prompt = f"""You are writing bridge content for an interactive visual novel / language learning game.
The player is a foreigner in {skeleton.setting}, learning {skeleton.target_language} to survive.

STORY TONE: {skeleton.tone}

WHAT JUST HAPPENED (from-anchor: "{from_anchor.title}"):
{from_anchor.generation_hint or "Hand-written scene completed."}

WHAT NEEDS TO HAPPEN NEXT (to-anchor: "{to_anchor.title}"):
{to_anchor.generation_hint or "The story continues."}

PLAYER STATE:
- Dominant personality: {dominant}
- Recent choices: {json.dumps(recent_choices, ensure_ascii=False)}
- Reputation: {json.dumps(reputation, ensure_ascii=False)}

CHARACTERS IN SCENE:
{chr(10).join(char_descriptions) if char_descriptions else "No specific characters."}

LOCATIONS:
{chr(10).join(loc_descriptions) if loc_descriptions else "Unspecified location."}
{learning_text}
META-NARRATIVE CONTEXT: {skeleton.meta_narrative}

Generate 3-6 bridge panels that transition from the previous scene to the next anchor point.

RULES:
1. Each panel must be a JSON object with these fields:
   - "id": unique string (use pattern "gen_{{from_anchor}}_{{number}}")
   - "image": null (images will be generated separately)
   - "aspect": "square" | "wide" | "tall"
   - "narration": string or null (narrator's prose, English, cinematic style)
   - "dialogue": string or null (character speech)
   - "speaker": string or null (character ID: "bimbo", "hana", "player", etc.)
2. Write in the established literary style — evocative, precise, atmospheric
3. Naturally weave in {skeleton.target_language} vocabulary when characters speak
4. Reflect the player's dominant personality in how NPCs react to them
5. Do NOT include options or branch_point mechanics — those only appear in hand-written anchors
6. Keep panels focused and tight — each advances the narrative meaningfully

Respond with ONLY a JSON array of panel objects. No markdown, no explanation."""

    return prompt


async def generate_segment(
    skeleton: StorySkeleton,
    from_anchor: Anchor,
    to_anchor: Anchor,
    player_state: dict,
    characters: dict = None,
    locations: dict = None,
) -> dict:
    """Generate bridge panels between two anchors.

    Returns:
        {
            "panels": [...],
            "generated": True/False,
            "cached": True/False,
        }
    """
    # If from_anchor has hand-written panels, return those directly
    if from_anchor.panels:
        return {
            "panels": from_anchor.panels,
            "generated": False,
            "cached": False,
        }

    # Check cache first
    state_hash = compute_state_hash(player_state or {})
    cached_panels = get_cached(skeleton.id, from_anchor.id, to_anchor.id, state_hash)
    if cached_panels:
        logger.info(f"[Generator] Cache hit: {from_anchor.id} -> {to_anchor.id} (hash={state_hash})")
        return {
            "panels": cached_panels,
            "generated": True,
            "cached": True,
        }

    # Generate with LLM
    logger.info(f"[Generator] Generating: {from_anchor.id} -> {to_anchor.id} (hash={state_hash})")

    characters = characters or {}
    locations = locations or {}

    prompt = _build_generation_prompt(
        skeleton, from_anchor, to_anchor, player_state or {}, characters, locations
    )

    try:
        panels = await _call_llm(prompt)

        # Cache the result
        set_cached(skeleton.id, from_anchor.id, to_anchor.id, state_hash, panels)

        return {
            "panels": panels,
            "generated": True,
            "cached": False,
        }
    except Exception as e:
        logger.error(f"[Generator] Generation failed: {e}")
        # Return a fallback panel
        return {
            "panels": [{
                "id": f"gen_{from_anchor.id}_fallback",
                "image": None,
                "aspect": "square",
                "narration": from_anchor.generation_hint or "The story continues...",
                "dialogue": None,
                "speaker": None,
            }],
            "generated": True,
            "cached": False,
        }


async def _call_llm(prompt: str) -> list[dict]:
    """Call GPT-4o to generate panels."""
    from openai import AsyncOpenAI

    api_key = config.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = AsyncOpenAI(api_key=api_key)
    model = getattr(config, "OPENAI_NARRATIVE_MODEL", "gpt-4o")

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content.strip()

    # Parse JSON — handle both array and object-wrapped-array
    data = json.loads(content)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "panels" in data:
        return data["panels"]
    if isinstance(data, dict):
        # Try to find an array value
        for v in data.values():
            if isinstance(v, list):
                return v

    raise ValueError(f"Unexpected LLM response format: {type(data)}")
