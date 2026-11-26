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


# --- M-1: the demo costs $0 per visitor -------------------------------------
# Scenes 1-8 of backend/scenarios.json are played through the real routes with
# DEMO_MODE on, while every paid provider entry point is replaced by a counter.

import json
from pathlib import Path

import pytest

SCENARIOS_JSON = Path(__file__).resolve().parents[1] / "backend" / "scenarios.json"
PROVIDER_FUNCS = (
    "transcribe_audio", "invoke_google", "openai_chat", "romanize",
    "makes_sense", "translate_text", "tts_with_openai",
)


@pytest.fixture
def provider_calls(monkeypatch):
    """Count every call into a paid provider (LLM, STT, TTS clients)."""
    providers = importlib.import_module("providers")
    calls: dict[str, int] = {}

    def counter(name, result):
        def fake(*args, **kwargs):
            calls[name] = calls.get(name, 0) + 1
            return result() if callable(result) else result
        return fake

    results = {
        "transcribe_audio": lambda: providers.TranscriptionResult(text="ぜんぜんちがう", provider="openai", model="stub"),
        "invoke_google": lambda: (type("R", (), {"content": "0"})(), 0),
        "openai_chat": "0",
        "romanize": "stub",
        "makes_sense": True,
        "translate_text": "stub",
        "tts_with_openai": b"tts-bytes",
    }
    for name in PROVIDER_FUNCS:
        monkeypatch.setattr(providers, name, counter(name, results[name]), raising=False)

    def client_boom(name):
        def fake(*args, **kwargs):
            calls[name] = calls.get(name, 0) + 1
            raise RuntimeError(f"{name} client must not be built in demo mode")
        return fake

    monkeypatch.setattr(importlib.import_module("voice.elevenlabs"), "get_client", client_boom("elevenlabs_client"))
    monkeypatch.setattr(importlib.import_module("voice.google"), "get_client", client_boom("google_tts_client"))
    return calls


@pytest.fixture
def builtin_scenarios(monkeypatch):
    scen = importlib.import_module("services.scenarios")
    data = json.loads(SCENARIOS_JSON.read_text(encoding="utf-8"))
    monkeypatch.setattr(scen, "scenarios_data", data)
    return {s["id"]: s for s in data if 1 <= int(s["id"]) <= 8}


def _demo(monkeypatch, on: bool):
    monkeypatch.setattr(importlib.import_module("config"), "DEMO_MODE", on, raising=False)


def test_demo_mode_scenes_1_to_8_make_no_provider_call(app_client, monkeypatch, provider_calls, builtin_scenarios):
    _demo(monkeypatch, True)
    assert sorted(builtin_scenarios) == list(range(1, 9))
    advanced_to = set()

    for sid, scene in sorted(builtin_scenarios.items()):
        # Spoken NPC line: a cache miss is skipped, never synthesised, on every TTS provider.
        for provider in ("elevenlabs", "google", "openai"):
            res = app_client.post("/api/tts", json={
                "text": scene["character_dialogue_jp"], "language": "Japanese",
                "provider": provider, "scenario_id": sid,
            })
            assert res.status_code == 200
            assert res.json() == {"skip": True, "reason": "demo_mode_tts_cache_only"}, (sid, provider, res.json())

        # Options panel: the scenario's own examples, no generation.
        res = app_client.get("/narrative/options", params={"scenario_id": sid, "lang": "Japanese", "native": "English"})
        assert res.status_code == 200
        body = res.json()
        assert [o["next_scenario"] for o in body["options"]] == [o["next_scenario"] for o in scene.get("options", [])]

        for opt in scene.get("options", []):
            said = opt["examples"][0]["target"]
            # Beginner "repeat after me" turn.
            res = app_client.post("/narrative/imitate", data={
                "expected": said, "next_scenario": str(opt["next_scenario"]), "lang": "Japanese", "transcript": said,
            })
            assert res.status_code == 200
            assert res.json()["success"] is True and res.json()["nextScenario"] == opt["next_scenario"]

            # Free-speech turn: matched locally (keywords / similarity), no audio uploaded.
            res = app_client.post("/narrative/interaction", data={
                "current_scenario_id": str(sid), "lang": "Japanese", "transcript": said,
            })
            assert res.status_code == 200
            out = res.json()
            assert out["nextScenario"]["id"] == opt["next_scenario"], (sid, said, out)
            assert out["match_type"] in {"yes_no_keyword", "polite_affirmative", "examples_similarity"}
            advanced_to.add(opt["next_scenario"])

        # Nonsense with an audio upload: no transcription, no LLM fallback, no romanization.
        if scene.get("options"):
            res = app_client.post(
                "/narrative/interaction",
                data={"current_scenario_id": str(sid), "lang": "Japanese", "transcript": "ぜんぜんちがうことば"},
                files={"audio_file": ("r.webm", b"\x1a\x45\xdf\xa3", "audio/webm")},
            )
            assert res.status_code == 200
            assert "nextScenario" not in res.json()

    assert advanced_to == {2, 3, 4, 5, 6, 7, 8}
    assert provider_calls == {}, f"demo mode reached paid providers: {provider_calls}"


def test_demo_mode_without_transcript_refuses_instead_of_transcribing(app_client, monkeypatch, provider_calls, builtin_scenarios):
    _demo(monkeypatch, True)
    res = app_client.post(
        "/narrative/interaction",
        data={"current_scenario_id": "1", "lang": "Japanese"},
        files={"audio_file": ("r.webm", b"\x1a\x45\xdf\xa3", "audio/webm")},
    )
    assert res.status_code == 200
    assert res.json()["error"] == "demo_mode_transcript_required"
    assert provider_calls == {}


def test_demo_mode_off_keeps_paid_paths(app_client, monkeypatch, provider_calls, builtin_scenarios):
    _demo(monkeypatch, False)
    audio = {"audio_file": ("r.webm", b"\x1a\x45\xdf\xa3", "audio/webm")}

    # The transcript field is ignored: the audio is transcribed, then the LLM is asked.
    res = app_client.post("/narrative/interaction", data={"current_scenario_id": "1", "lang": "Japanese", "transcript": "はい"}, files=audio)
    assert res.status_code == 200
    assert res.json()["heard"] == "ぜんぜんちがう"
    assert provider_calls.get("transcribe_audio") == 1
    assert provider_calls.get("invoke_google") == 1

    res = app_client.post("/narrative/imitate", data={"expected": "はい", "lang": "Japanese", "transcript": "はい"}, files=audio)
    assert res.status_code == 200 and res.json()["heard"] == "ぜんぜんちがう"
    assert provider_calls.get("transcribe_audio") == 2
    assert provider_calls.get("makes_sense") == 1

    # Audio stays required outside demo mode.
    assert app_client.post("/narrative/interaction", data={"current_scenario_id": "1", "transcript": "はい"}).status_code == 422
    assert app_client.post("/narrative/imitate", data={"expected": "はい", "transcript": "はい"}).status_code == 422

    # Options are generated by the LLM; a TTS miss is synthesised.
    app_client.get("/narrative/options", params={"scenario_id": 1})
    assert provider_calls.get("invoke_google") == 2
    before = provider_calls.get("tts_with_openai", 0)
    res = app_client.post("/api/tts", json={"text": "demo off phrase", "language": "Japanese", "provider": "openai"})
    assert res.status_code == 200 and res.json().get("provider") == "openai"
    assert provider_calls.get("tts_with_openai") == before + 1
