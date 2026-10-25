"""Contract test for the /api/practice/scenarios endpoint.

Verifies the 3 pre-authored beginner Mandarin scenarios (queue item
langhero-practice/scenarios) are served for the /practice starter menu.
"""

from __future__ import annotations


SCENARIOS_PATH = "/api/practice/scenarios"


def test_practice_scenarios_returns_three_items(app_client):
    r = app_client.get(SCENARIOS_PATH)
    assert r.status_code == 200, r.text
    body = r.json()

    assert isinstance(body, list)
    assert len(body) == 3

    for scenario in body:
        assert isinstance(scenario.get("id"), str) and scenario["id"]
        assert isinstance(scenario.get("title"), str) and scenario["title"]
        assert scenario.get("target_language") == "Mandarin Chinese"

        starter_turns = scenario.get("starter_turns")
        assert isinstance(starter_turns, list) and len(starter_turns) > 0
        assert starter_turns[0]["role"] == "tutor"
