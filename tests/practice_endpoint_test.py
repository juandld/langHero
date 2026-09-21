"""Contract test for the /api/practice/chat endpoint.

This defines v1c of the /practice route: live conversation with an LLM tutor
+ per-utterance Jev scoring on 4 calibrated dimensions.

Skipped gracefully until the backend route lands (queue item
langhero-practice/backend).
"""

from __future__ import annotations

import pytest


PRACTICE_PATH = "/api/practice/chat"


def _endpoint_present(client) -> bool:
    r = client.post(PRACTICE_PATH, json={})
    return r.status_code != 404


def test_practice_chat_contract(app_client):
    """POST returns tutor turn + 4 calibrated scores + one alternative."""
    if not _endpoint_present(app_client):
        pytest.skip(f"{PRACTICE_PATH} not implemented yet — queue item langhero-practice/backend")

    payload = {
        "target_language": "Mandarin Chinese",
        "history": [
            {"role": "tutor", "text": "你想喝什么?", "translation": "What do you want to drink?"},
        ],
        "user_message": "我要一个啤酒",
        "user_intent": "I want a beer",
        "scenario": "ordering at a Beijing bar, casual register",
    }
    r = app_client.post(PRACTICE_PATH, json=payload)
    assert r.status_code == 200, r.text
    body = r.json()

    # Tutor turn — string, non-empty, in the target language.
    assert isinstance(body.get("tutor_turn"), str)
    assert len(body["tutor_turn"]) > 0

    # Scores — dict of 4 dims, each 0..1.
    scores = body.get("scores")
    assert isinstance(scores, dict)
    for dim in ("grammatical", "natural", "register", "meaning"):
        assert dim in scores, f"missing score dim: {dim}"
        v = scores[dim]
        assert isinstance(v, (int, float))
        assert 0.0 <= v <= 1.0, f"score {dim}={v} out of [0,1]"

    # One suggested alternative from a native speaker (string, may be empty
    # if the learner nailed it — in that case scores.natural should be >= 0.9).
    assert "alternative" in body
    assert isinstance(body["alternative"], str)
    if body["alternative"] == "":
        assert scores["natural"] >= 0.9


def test_practice_chat_low_scores_on_ungrammatical(app_client):
    """Deliberately broken input drags grammatical score below 0.5."""
    if not _endpoint_present(app_client):
        pytest.skip(f"{PRACTICE_PATH} not implemented yet")

    payload = {
        "target_language": "Mandarin Chinese",
        "history": [],
        "user_message": "我 啤酒 要 的",  # word soup
        "user_intent": "I want a beer",
        "scenario": "ordering at a bar",
    }
    r = app_client.post(PRACTICE_PATH, json=payload)
    assert r.status_code == 200
    scores = r.json()["scores"]
    assert scores["grammatical"] < 0.5, f"expected low grammatical, got {scores}"


def test_practice_chat_high_scores_on_native_response(app_client):
    """Idiomatic native response should score high on all 4 dims."""
    if not _endpoint_present(app_client):
        pytest.skip(f"{PRACTICE_PATH} not implemented yet")

    payload = {
        "target_language": "Mandarin Chinese",
        "history": [
            {"role": "tutor", "text": "你想喝什么?", "translation": "What do you want to drink?"},
        ],
        "user_message": "来一瓶啤酒",  # natural casual "gimme a beer"
        "user_intent": "I want a beer",
        "scenario": "ordering at a Beijing bar, casual register",
    }
    r = app_client.post(PRACTICE_PATH, json=payload)
    assert r.status_code == 200
    scores = r.json()["scores"]
    assert scores["grammatical"] >= 0.7
    assert scores["natural"] >= 0.7
    assert scores["register"] >= 0.7
    assert scores["meaning"] >= 0.7
