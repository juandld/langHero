import importlib


def test_demo_mode_story_import_skips_llm(monkeypatch):
    cfg = importlib.import_module("config")
    story_import = importlib.import_module("story_import")

    monkeypatch.setattr(cfg, "DEMO_MODE", True, raising=False)
    monkeypatch.setattr(cfg, "DEMO_ALLOW_LLM_IMPORT", False, raising=False)

    def boom(*args, **kwargs):
        raise AssertionError("LLM path should not be called in demo mode")

    monkeypatch.setattr(story_import, "generate_scenarios_from_transcript", boom, raising=True)

    scenarios, lang = story_import.build_imported_scenarios(text="Line one.\nLine two.", target_language="Japanese", max_scenes=3)
    assert lang == "Japanese"
    assert isinstance(scenarios, list) and scenarios
    assert any((s.get("mode") == "advanced") for s in scenarios if isinstance(s, dict))


def test_demo_mode_from_video_requires_cache(app_client, monkeypatch):
    cfg = importlib.import_module("config")
    # generate_scenarios_from_video was moved from main.py into
    # backend/services/video.py; the route handler at
    # backend/routes/import_routes.py:17 imports it directly, so the patch
    # must land on the route module's local binding to intercept the call.
    import_routes_mod = importlib.import_module("routes.import_routes")

    monkeypatch.setattr(cfg, "DEMO_MODE", True, raising=False)
    monkeypatch.setattr(cfg, "DEMO_VIDEO_CACHE_ONLY", True, raising=False)

    def boom(*args, **kwargs):
        raise AssertionError("from_video generator should not be called on cache-only rejection")

    monkeypatch.setattr(import_routes_mod, "generate_scenarios_from_video", boom, raising=True)

    res = app_client.post(
        "/api/scenarios/from_video",
        json={
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "target_language": "Japanese",
            "max_scenes": 3,
            "activate": False,
            "attest_rights": True,
        },
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "demo_mode_cache_only"
