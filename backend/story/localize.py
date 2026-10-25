"""
Panel Localizer — renders existing panels (hand-written or generated) in a
target narration language at a chosen vocabulary level, without touching
story structure.

Keeps "same story, different vocabulary": only text fields (narration,
dialogue, option labels) are rewritten. Panel ids, images, branch config,
next_panel/next_anchor pointers, and example phrase pairs are passed through
unchanged so the underlying plot graph never shifts.
"""

import hashlib
import json
import logging
import os
from typing import Optional

import config

logger = logging.getLogger(__name__)

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "localize_cache")

# Reuse the same difficulty ladder as LearningObjective.difficulty so a
# player's self-reported level maps onto the same vocabulary — just applied
# to the OUTPUT language instead of the embedded target-language words.
LEVELS = ["beginner", "elementary", "intermediate", "advanced"]

_LEVEL_GUIDANCE = {
    "beginner": "Use only the ~500 most common words. Short sentences (max ~8 words). Present tense preferred. No idioms.",
    "elementary": "Use common everyday vocabulary. Sentences up to ~12 words. Simple past/future allowed. Avoid idioms.",
    "intermediate": "Natural conversational vocabulary, some idioms. Sentences can be compound. Varied tenses.",
    "advanced": "Full native-level vocabulary, idioms, subordinate clauses, literary register matching the original tone.",
}

# "Native language" == default fallback when no language override requested.
DEFAULT_LANGUAGE = "en"


def _ensure_cache_dir():
    os.makedirs(CACHE_DIR, exist_ok=True)


def _content_hash(panels: list[dict]) -> str:
    raw = json.dumps(panels, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _cache_path(story_id: str, anchor_id: str, language: str, level: str, content_hash: str) -> str:
    key = f"{story_id}__{anchor_id}__{language}__{level}__{content_hash}"
    return os.path.join(CACHE_DIR, f"{key}.json")


def _get_cached(path: str) -> Optional[list[dict]]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f).get("panels")
    except (json.JSONDecodeError, OSError):
        return None


def _set_cached(path: str, panels: list[dict]):
    _ensure_cache_dir()
    with open(path, "w") as f:
        json.dump({"panels": panels}, f, ensure_ascii=False, indent=2)


def needs_localization(language: Optional[str], level: Optional[str]) -> bool:
    if not language:
        return False
    return language.strip().lower() not in ("", DEFAULT_LANGUAGE, "english")


def _extract_text_units(panels: list[dict]) -> list[dict]:
    """Pull out only the translatable text fields, tagged by index path."""
    units = []
    for p_idx, panel in enumerate(panels):
        if panel.get("narration"):
            units.append({"path": [p_idx, "narration"], "text": panel["narration"]})
        if panel.get("dialogue"):
            units.append({"path": [p_idx, "dialogue"], "text": panel["dialogue"]})
        for o_idx, option in enumerate(panel.get("options") or []):
            if option.get("text"):
                units.append({"path": [p_idx, "options", o_idx, "text"], "text": option["text"]})
            # `examples[].native` is the player-facing gloss of the target-language
            # phrase (e.g. "I am a castaway" next to the Japanese). It's shown
            # directly in the choice UI, so it must localize too — only
            # `.target` (the language being learned) and `.pronunciation` stay
            # untouched, since those aren't narration-language text.
            for e_idx, example in enumerate(option.get("examples") or []):
                if example.get("native"):
                    units.append({
                        "path": [p_idx, "options", o_idx, "examples", e_idx, "native"],
                        "text": example["native"],
                    })
        variants = panel.get("choice_variants") or {}
        for src_id, by_choice in variants.items():
            for choice_key, fields in by_choice.items():
                if fields.get("dialogue"):
                    units.append({
                        "path": [p_idx, "choice_variants", src_id, choice_key, "dialogue"],
                        "text": fields["dialogue"],
                    })
    return units


def _apply_text_units(panels: list[dict], units: list[dict], translations: dict) -> list[dict]:
    """Write translated strings back into a deep copy of panels."""
    out = json.loads(json.dumps(panels, ensure_ascii=False))
    for i, unit in enumerate(units):
        translated = translations.get(str(i))
        if not translated:
            continue
        node = out
        path = unit["path"]
        for step in path[:-1]:
            node = node[step]
        node[path[-1]] = translated
    return out


async def localize_panels(
    panels: list[dict],
    language: str,
    level: str,
    setting: str = "",
) -> list[dict]:
    """Return panels with narration/dialogue/option text rewritten into
    `language` at `level` vocabulary complexity. Structure is untouched.
    """
    if not panels or not needs_localization(language, level):
        return panels

    level = level if level in LEVELS else "beginner"
    units = _extract_text_units(panels)
    if not units:
        return panels

    content_hash = _content_hash(panels)
    story_id = panels[0].get("id", "panel") if panels else "panel"
    cache_file = _cache_path(story_id, panels[0].get("id", "x"), language, level, content_hash)
    cached = _get_cached(cache_file)
    if cached is not None:
        return cached

    try:
        translations = await _call_llm_translate(units, language, level, setting)
    except Exception as e:
        logger.error(f"[Localize] Translation failed, returning original panels: {e}")
        return panels

    localized = _apply_text_units(panels, units, translations)
    _set_cached(cache_file, localized)
    return localized


async def _call_llm_translate(units: list[dict], language: str, level: str, setting: str) -> dict:
    from openai import AsyncOpenAI

    api_key = config.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = AsyncOpenAI(api_key=api_key)
    model = getattr(config, "OPENAI_NARRATIVE_MODEL", "gpt-4o")

    guidance = _LEVEL_GUIDANCE.get(level, _LEVEL_GUIDANCE["beginner"])
    numbered = {str(i): u["text"] for i, u in enumerate(units)}

    prompt = f"""You are localizing an interactive story game into {language} for a
language-immersion learner at the "{level}" vocabulary level.

Setting: {setting or "unspecified"}

VOCABULARY LEVEL RULES: {guidance}

Rewrite EACH of the following strings into natural {language}, matching the
tone and meaning of the original, following the vocabulary level rules.
Keep the SAME plot meaning and the SAME number of strings — do not merge,
split, add, or remove items, and do not change what the story means.

Input (JSON object, id -> original text):
{json.dumps(numbered, ensure_ascii=False, indent=2)}

Respond with ONLY a JSON object mapping the same ids to the localized text."""

    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=4000,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content.strip()
    data = json.loads(content)
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected translation response format: {type(data)}")
    return data
