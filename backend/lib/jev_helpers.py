"""Higher-level Jev callers for langHero.

Each helper bundles 3-4 noul questions in a single Jev call — the capability
probe showed bundled calls carry the same latency as a single question, so
packing is free. Helpers never raise on Jev errors; a Jev outage returns {}
and skips the log, so the practice route never fails because of a grader.
"""

from __future__ import annotations

import time

from lib import grade_log, jev_client
from practice_scoring import _clamp01, mock_enabled

MOCK_TUTOR_SCORES = {"register_fits": 0.9, "naturalness": 0.85, "level_appropriate": 0.9}


def grade_tutor_line(
    *,
    scenario: str,
    target_language: str,
    tutor_line: str,
    learner_level: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Score an AI tutor line on 3 dims (register, naturalness, level fit).

    Log-only — scores are inserted into `jev_grades`; nothing gates on them.
    Returns {} if Jev is unreachable or the call fails.
    """
    if mock_enabled():
        return MOCK_TUTOR_SCORES

    state = {
        "scenario": scenario,
        "target_language": target_language,
        "tutor_line": tutor_line,
        "learner_level": learner_level or "unspecified (default to A2)",
        "session_id": session_id,
    }
    questions = {
        "register_fits": {
            "type": "noul",
            "instructions": (
                f"Does this {target_language} tutor line match the register appropriate "
                "for the scenario? 1 if a native speaker would say this here, 0 if the "
                "register is wrong for the setting."
            ),
        },
        "naturalness": {
            "type": "noul",
            "instructions": (
                f"Would a native {target_language} speaker say this naturally, or does it "
                "sound like a textbook phrase? 1=natural, 0=stilted."
            ),
        },
        "level_appropriate": {
            "type": "noul",
            "instructions": (
                "Given the learner's level (default A2 if unspecified), is this tutor line "
                "appropriately challenging? 1=yes, 0=too hard or too easy."
            ),
        },
    }

    t0 = time.perf_counter()
    try:
        answers = jev_client.call(state=state, questions=questions)
    except jev_client.JevError:
        return {}
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    scores = {dim: _clamp01((answers.get(dim) or {}).get("noul")) for dim in questions}
    grade_log.log_grade(
        grader="tutor_line",
        target_language=target_language,
        state=state,
        scores=scores,
        latency_ms=latency_ms,
    )
    return scores


def grade_authored_line(
    *,
    scenario: str,
    target_language: str,
    line: str,
    grader_name: str,
    speaker: str | None = None,
    source_id: str | None = None,
    learner_level: str | None = None,
) -> dict:
    """Score a pre-authored target-language line (dialogue script, legacy scene).

    Same 3 noul questions as grade_tutor_line, but tagged under a caller-supplied
    grader_name so the SQLite log can be queried per source. Log-only; swallows
    Jev errors.
    """
    if mock_enabled():
        return MOCK_TUTOR_SCORES

    state = {
        "scenario": scenario,
        "target_language": target_language,
        "tutor_line": line,
        "learner_level": learner_level or "unspecified (default to A2)",
        "speaker": speaker or "unspecified",
        "source_id": source_id or "unspecified",
    }
    questions = {
        "register_fits": {
            "type": "noul",
            "instructions": (
                f"Does this {target_language} line match the register appropriate "
                "for the scenario? 1 if a native speaker would say this here, 0 if the "
                "register is wrong for the setting."
            ),
        },
        "naturalness": {
            "type": "noul",
            "instructions": (
                f"Would a native {target_language} speaker say this naturally, or does it "
                "sound like a textbook phrase? 1=natural, 0=stilted."
            ),
        },
        "level_appropriate": {
            "type": "noul",
            "instructions": (
                "Given the learner's level (default A2 if unspecified), is this line "
                "appropriately challenging to encounter? 1=yes, 0=too hard or too easy."
            ),
        },
    }

    t0 = time.perf_counter()
    try:
        answers = jev_client.call(state=state, questions=questions)
    except jev_client.JevError:
        return {}
    latency_ms = round((time.perf_counter() - t0) * 1000, 1)

    scores = {dim: _clamp01((answers.get(dim) or {}).get("noul")) for dim in questions}
    grade_log.log_grade(
        grader=grader_name,
        target_language=target_language,
        state=state,
        scores=scores,
        latency_ms=latency_ms,
    )
    return scores
