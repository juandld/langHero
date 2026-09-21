"""Contract test for the Jev-backed learner-utterance scorer.

Lives in backend/practice_scoring.py. Wraps the shared Jev client so
practice_endpoint (and any future async batch grader) has a single
call surface.

Skips gracefully when either the module or JEV_API_TOKEN is missing.
"""

from __future__ import annotations

import importlib
import os

import pytest


def _module():
    try:
        return importlib.import_module("practice_scoring")
    except ImportError:
        pytest.skip("backend/practice_scoring.py not present yet — queue item langhero-practice/jev")


def _skip_without_jev():
    if not os.environ.get("JEV_API_TOKEN"):
        pytest.skip("JEV_API_TOKEN not set in test env — Jev live call skipped")


def test_score_signature_and_shape():
    mod = _module()
    _skip_without_jev()

    result = mod.score_utterance(
        target_language="Mandarin Chinese",
        scenario="ordering at a Beijing bar, casual register",
        history=[],
        user_intent="I want a beer",
        utterance="来一瓶啤酒",
    )

    for dim in ("grammatical", "natural", "register", "meaning"):
        assert dim in result, f"missing dim {dim}"
        assert 0.0 <= float(result[dim]) <= 1.0

    assert "alternative" in result
    assert isinstance(result["alternative"], str)


def test_score_native_response_scores_high():
    mod = _module()
    _skip_without_jev()

    result = mod.score_utterance(
        target_language="Mandarin Chinese",
        scenario="ordering at a Beijing bar, casual register",
        history=[],
        user_intent="I want a beer",
        utterance="来一瓶啤酒",
    )
    assert result["natural"] >= 0.7


def test_score_word_soup_scores_low_grammatical():
    mod = _module()
    _skip_without_jev()

    result = mod.score_utterance(
        target_language="Mandarin Chinese",
        scenario="ordering at a bar",
        history=[],
        user_intent="I want a beer",
        utterance="我 啤酒 要 的",
    )
    assert result["grammatical"] < 0.5
