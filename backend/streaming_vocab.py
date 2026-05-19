"""Vocab matching and comparison logic for streaming sessions.

Extracted from streaming.py to keep each module under ~300 lines.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict

import providers
from language import detect_language_from_text

logger = logging.getLogger(__name__)


def _quick_translate(text: str, source: str = "Japanese", target: str = "English") -> str:
    """Translate a short phrase using OpenAI. Best-effort, returns empty on failure."""
    if not text or not text.strip():
        return ""
    try:
        import config as cfg
        if not cfg.OPENAI_API_KEY:
            return ""
        from openai import OpenAI
        client = OpenAI(api_key=cfg.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Translate this {source} text to literal {target}. Reply with ONLY the translation, nothing else. If the input is gibberish, translate it as literally as possible — the humor matters."},
                {"role": "user", "content": text},
            ],
            max_tokens=60,
            temperature=0,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.debug("Quick translate failed: %s", e)
        return ""


def _vocab_match_level(transcript: str, expected: str) -> float:
    """Calculate match level between transcript and expected phrase."""
    def normalize(s: str) -> str:
        s = re.sub(r'[^\w\s]', '', s.lower().strip())
        return ''.join(s.split())

    norm_transcript = normalize(transcript)
    norm_expected = normalize(expected)

    if not norm_transcript or not norm_expected:
        return 0.0
    if norm_transcript == norm_expected:
        return 1.0
    if norm_expected in norm_transcript or norm_transcript in norm_expected:
        return min(len(norm_transcript), len(norm_expected)) / max(len(norm_transcript), len(norm_expected))
    common = sum(1 for c in norm_expected if c in norm_transcript)
    return common / max(len(norm_expected), 1)


def compute_outcome_tier(match_level: float, transcript: str, target_language: str) -> str:
    """Compute outcome tier from match level and detected language.

    Returns: 'perfect', 'good', 'passable', 'fumble', or 'fail'
    """
    if not transcript or not transcript.strip():
        return "fail"

    detected = detect_language_from_text(transcript)
    correct_lang = (detected == target_language) or detected == "unknown"

    if match_level >= 0.9:
        return "perfect"
    if match_level >= 0.7:
        return "good"
    if match_level >= 0.35 and correct_lang:
        return "passable"
    if correct_lang:
        return "fumble"
    return "fail"


def compare_vocab_response(transcript: str, expected: str, tag: str = "", target_language: str = "japanese") -> Dict[str, Any]:
    """Compare a transcript to an expected vocab phrase."""
    if not transcript or not transcript.strip():
        logger.info("[%s] compare_vocab_response: no speech detected", tag)
        return {
            "error": "no_speech_detected",
            "heard": transcript,
            "expected": expected,
            "match_level": 0.0,
            "score": 0,
            "tier": "fail",
            "detected_language": "unknown",
        }

    match_level = _vocab_match_level(transcript, expected)
    detected = detect_language_from_text(transcript)
    tier = compute_outcome_tier(match_level, transcript, target_language)
    success = tier in ("perfect", "good")
    logger.info("[%s] compare_vocab: heard=%r expected=%r match=%.3f tier=%s detected=%s", tag, transcript[:80], expected[:80], match_level, tier, detected)
    heard_translation = "" if success else _quick_translate(transcript)
    try:
        heard_pronunciation = providers.romanize(transcript, "Japanese") if transcript.strip() else ""
    except Exception:
        heard_pronunciation = ""

    return {
        "heard": transcript,
        "heard_translation": heard_translation,
        "heard_pronunciation": heard_pronunciation,
        "expected": expected,
        "match_level": match_level,
        "score": int(match_level * 100),
        "nextScenario": True if tier in ("perfect", "good", "passable") else None,
        "success": success,
        "tier": tier,
        "detected_language": detected,
    }


def compare_vocab_multi(transcript: str, expected_list: list, tag: str = "", target_language: str = "japanese") -> Dict[str, Any]:
    """Compare a transcript against multiple expected phrases, return best match."""
    if not transcript or not transcript.strip():
        logger.info("[%s] compare_vocab_multi: no speech detected", tag)
        return {
            "error": "no_speech_detected",
            "heard": transcript,
            "expected": expected_list[0] if expected_list else "",
            "match_level": 0.0,
            "score": 0,
            "matched_index": -1,
            "tier": "fail",
            "detected_language": "unknown",
        }

    best_level = 0.0
    best_index = 0
    scores = []
    for i, expected in enumerate(expected_list):
        level = _vocab_match_level(transcript, expected)
        scores.append((i, level, expected))
        if level > best_level:
            best_level = level
            best_index = i

    logger.info("[%s] compare_vocab_multi: heard=%r | scores=%s", tag, transcript[:80],
                " | ".join(f"[{i}] {lvl:.3f} {exp[:30]}" for i, lvl, exp in scores))

    detected = detect_language_from_text(transcript)
    tier = compute_outcome_tier(best_level, transcript, target_language)
    success = tier in ("perfect", "good")
    logger.info("[%s] compare_vocab_multi: best_index=%d best_level=%.3f tier=%s detected=%s", tag, best_index, best_level, tier, detected)

    heard_translation = "" if success else _quick_translate(transcript)
    try:
        heard_pronunciation = providers.romanize(transcript, "Japanese") if transcript.strip() else ""
    except Exception:
        heard_pronunciation = ""

    return {
        "heard": transcript,
        "heard_translation": heard_translation,
        "heard_pronunciation": heard_pronunciation,
        "expected": expected_list[best_index],
        "match_level": best_level,
        "score": int(best_level * 100),
        "nextScenario": True if tier in ("perfect", "good", "passable") else None,
        "success": success,
        "matched_index": best_index,
        "tier": tier,
        "detected_language": detected,
    }
