"""Jev capability probe — detects drift in what Jev will and won't score.

Established baselines (2026-10-15, jev-latest, 6 live calls):

  P1  Register of a BAD tutor line (archaic 阁下 at a dumpling stall)
      → 0.06 (deterministic across 3 identical calls: 0.06, 0.06, 0.05)
      Jev is sharp on register when state carries the Mandarin + scene.

  P2  Pacing from an events_ms list (TTS starts 520ms after typewriter)
      → ~0.52 / 0.54 (hedged neutral; same for the inverse question)
      HARD WALL: Jev will not reason about time deltas described as text.
      Timing/sync observability must not rely on Jev.

  P3  Mood coherence of a *described* chapter transition (frames as text)
      → 0.90 / 0.95
      Perceptual visual scoring works IF we pre-describe frames via vision LLM.

  P4  4 noul questions bundled in one call
      → 62ms (same latency as a single-question call)
      Bundling is free; always pack 3-4 related axes per call.

Run:
    python3 backend/scripts/jev_capability_probe.py

Flags a FAIL if any baseline-shifts beyond tolerance — rerun on new Jev
versions to catch capability drift (positive OR negative).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib import jev_client  # noqa: E402


def _call(state: Any, questions: dict) -> dict:
    t0 = time.perf_counter()
    try:
        answers = jev_client.call(state=state, questions=questions, max_retries=1, timeout=25)
        return {"ok": True, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), "answers": answers}
    except jev_client.JevError as e:
        return {"ok": False, "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
                "error": type(e).__name__, "detail": str(e)[:300]}


BAD_TUTOR_STATE = {
    "scenario": "A learner is buying xiaolongbao at a dumpling stall in Shanghai. "
                "Casual street-food setting. Vendor is friendly but busy.",
    "tutor_line_mandarin": "阁下想要几笼?",  # overly formal, archaic 阁下
    "tutor_line_pinyin": "gé xià xiǎng yào jǐ lóng?",
    "tutor_line_english_gloss": "How many steamers would your esteemed self like?",
}
REGISTER_QUESTION = {
    "register_fits_scene": {
        "type": "noul",
        "instructions": "Does the tutor's Mandarin line match the register appropriate "
                        "for this casual street-food scene? Score 1 if a native speaker "
                        "would say this here, 0 if the register is wrong for the setting.",
    }
}

TIMING_STATE = {
    "scene": "A learning app shows a story panel. A character line appears with "
             "typewriter animation while a TTS voice reads it aloud.",
    "events_ms": [
        {"t_ms": 0, "event": "panel displayed"},
        {"t_ms": 120, "event": "typewriter starts for 42-char line"},
        {"t_ms": 640, "event": "TTS audio begins"},
        {"t_ms": 4200, "event": "typewriter completes"},
        {"t_ms": 4950, "event": "TTS audio ends"},
    ],
}
TIMING_QUESTION = {
    "sync_feels_tight": {
        "type": "noul",
        "instructions": "Looking at the events timeline, would a learner feel the "
                        "typewriter and TTS audio were well-synchronised? 1=tight, "
                        "0=distracting drift.",
    }
}

TRANSITION_STATE = {
    "transition_purpose": "End of ch1 (betrayal) → start of ch2 (mountain escape).",
    "frames_described": [
        {"t": "start", "description": "Three characters in a dim indoor room, red lantern light, tense posture."},
        {"t": "mid", "description": "Full-screen gradient: red top, mountain-grey bottom, 'CHAPTER 2' centred white."},
        {"t": "end", "description": "Wide outdoor shot: single character on cliff edge, cold blue morning light, mist."},
    ],
    "intended_mood_shift": "Betrayed intimacy → cold solitude.",
}
TRANSITION_QUESTION = {
    "mood_shift_reads_coherent": {
        "type": "noul",
        "instructions": "Does this transition — described starting frame, mid frame, "
                        "ending frame — land the intended mood shift? 1=coherent story, "
                        "0=disconnected or unclear.",
    }
}

# Set-phrase probe (P4) — hypothesis under test: Jev may systematically under-
# score canonical formal set-phrases in casual contexts even though native
# speakers use them identically. Flagged after the full pass marked いらっしゃいませ /
# どうぞ召し上がれ / またお待ちしています as nat 0.45-0.57 in authored ramen scenes.
# This probe scores each phrase in BOTH casual and formal contexts. If both
# score ≥0.65 → Jev understands set-phrases are context-neutral. If casual
# scores are systematically lower → calibrate authored-content thresholds.
SETPHRASE_STATE = {
    "phrases": {
        "irasshaimase": {
            "text": "いらっしゃいませ！",
            "literal_english": "Welcome!",
            "notes": "Canonical greeting Japanese shop staff use when a customer enters.",
        },
        "douzo_meshiagare": {
            "text": "どうぞ召し上がれ！",
            "literal_english": "Please enjoy your meal!",
            "notes": "Said when serving food. Universally natural across most registers.",
        },
        "mata_omachi_shiteimasu": {
            "text": "またお待ちしています！",
            "literal_english": "We'll be waiting for you (come back soon)!",
            "notes": "Said as a customer leaves. Standard across shop types.",
        },
    },
    "contexts": {
        "casual_stall": "Cozy neighbourhood ramen stall in the evening. Chef is friendly, informal, busy.",
        "formal_kaiseki": "Formal kaiseki restaurant with multi-course omakase meal. Hushed, elegant setting.",
    },
}


def _setphrase_q(phrase_key: str, context_key: str) -> dict:
    return {
        "type": "noul",
        "instructions": (
            f"In the '{context_key}' context (see state.contexts.{context_key}), would a native "
            f"Japanese speaker consider phrases.{phrase_key}.text natural and register-appropriate? "
            "1 = yes, used naturally; 0 = unnatural or wrong register."
        ),
    }


SETPHRASE_QUESTIONS = {
    "irasshaimase_in_casual":        _setphrase_q("irasshaimase", "casual_stall"),
    "irasshaimase_in_formal":        _setphrase_q("irasshaimase", "formal_kaiseki"),
    "douzo_in_casual":               _setphrase_q("douzo_meshiagare", "casual_stall"),
    "douzo_in_formal":               _setphrase_q("douzo_meshiagare", "formal_kaiseki"),
    "mata_in_casual":                _setphrase_q("mata_omachi_shiteimasu", "casual_stall"),
    "mata_in_formal":                _setphrase_q("mata_omachi_shiteimasu", "formal_kaiseki"),
}


def _check(label: str, actual: float | None, expected_lo: float, expected_hi: float) -> tuple[bool, str]:
    if actual is None:
        return False, f"{label}: NO RESPONSE"
    ok = expected_lo <= actual <= expected_hi
    tag = "OK " if ok else "FAIL"
    return ok, f"[{tag}] {label}: got {actual:.3f}, expected [{expected_lo}, {expected_hi}]"


def main() -> int:
    print("Running Jev capability probe…\n")

    p1 = _call(BAD_TUTOR_STATE, REGISTER_QUESTION)
    p2 = _call(TIMING_STATE, TIMING_QUESTION)
    p3 = _call(TRANSITION_STATE, TRANSITION_QUESTION)
    p4 = _call(SETPHRASE_STATE, SETPHRASE_QUESTIONS)

    print(json.dumps({"P1": p1, "P2": p2, "P3": p3, "P4_setphrase": p4}, indent=2, ensure_ascii=False))
    print()

    p4_answers = p4.get("answers") or {} if p4["ok"] else {}
    def _p4(k: str) -> float | None:
        return (p4_answers.get(k) or {}).get("noul") if p4_answers else None

    checks = [
        _check(
            "P1 register (bad line) stays low",
            (p1.get("answers") or {}).get("register_fits_scene", {}).get("noul") if p1["ok"] else None,
            0.0, 0.25,
        ),
        _check(
            "P2 timing wall persists (neutral band)",
            (p2.get("answers") or {}).get("sync_feels_tight", {}).get("noul") if p2["ok"] else None,
            0.35, 0.65,
        ),
        _check(
            "P3 described transition reads coherent",
            (p3.get("answers") or {}).get("mood_shift_reads_coherent", {}).get("noul") if p3["ok"] else None,
            0.75, 1.0,
        ),
        _check("P4 setphrase いらっしゃいませ (casual)",     _p4("irasshaimase_in_casual"), 0.65, 1.0),
        _check("P4 setphrase いらっしゃいませ (formal)",     _p4("irasshaimase_in_formal"), 0.65, 1.0),
        _check("P4 setphrase どうぞ召し上がれ (casual)",       _p4("douzo_in_casual"),        0.65, 1.0),
        _check("P4 setphrase どうぞ召し上がれ (formal)",       _p4("douzo_in_formal"),        0.65, 1.0),
        # またお待ちしています scores 0.52/0.58 measured 2026-10-15. Native speakers use
        # it universally in shop farewells, but Jev consistently under-scores it —
        # a known weakness captured here as a calibrated threshold rather than a
        # failing gate. Authored content using this phrase should expect similar
        # low scores and not be flagged as defective purely on that signal.
        _check("P4 setphrase またお待ちしています (casual, known-weak)", _p4("mata_in_casual"), 0.45, 1.0),
        _check("P4 setphrase またお待ちしています (formal, known-weak)", _p4("mata_in_formal"), 0.45, 1.0),
    ]
    print("\nBaselines:")
    for _ok, msg in checks:
        print(f"  {msg}")

    failed = [msg for ok, msg in checks if not ok]
    if failed:
        print(f"\n{len(failed)} baseline(s) shifted — Jev capability may have drifted.")
        return 1
    print("\nAll baselines hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
