"""Every wired AI service books exactly one row in the AI-calls ledger (lib/ai_calls).

Each test stubs the provider client (no network, no paid call) and points AI_CALLS_LEDGER at
its own temp file, then drives the real langHero call site.
"""
from __future__ import annotations

import json
import sys
import types

import pytest

import config
import providers
from lib import ai_calls

# conftest stubs providers.invoke_google per test; keep the real one (captured at collection).
_REAL_INVOKE_GOOGLE = providers.invoke_google


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    path = tmp_path / "ledger.jsonl"
    monkeypatch.setenv("AI_CALLS_LEDGER", str(path))

    def rows() -> list[dict]:
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]

    return rows


def test_openai_chat_books_one_row(ledger, monkeypatch):
    import streaming_vocab

    usage = types.SimpleNamespace(prompt_tokens=21, completion_tokens=4)
    msg = types.SimpleNamespace(content=" hello ")
    resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)], usage=usage)

    class FakeOpenAI:
        def __init__(self, **_):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(create=lambda **kw: resp)
            )

    monkeypatch.setattr(config, "OPENAI_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))

    assert streaming_vocab._quick_translate("こんにちは") == "hello"
    rows = ledger()
    assert len(rows) == 1
    row = rows[0]
    assert (row["service"], row["model"], row["caller"]) == (
        "openai", "gpt-4o-mini", "langHero:vocab_quick_translate"
    )
    assert (row["input_tokens"], row["output_tokens"], row["ok"]) == (21, 4, True)


def test_gemini_books_one_row(ledger, monkeypatch):
    class FakeLLM:
        def invoke(self, messages, max_retries=0):
            return types.SimpleNamespace(
                content="ok", usage_metadata={"input_tokens": 9, "output_tokens": 2}
            )

    monkeypatch.setattr(providers, "invoke_google", _REAL_INVOKE_GOOGLE)
    monkeypatch.setattr(providers, "GOOGLE_LLMS", [FakeLLM()])
    resp, idx = providers.invoke_google(["hi"])
    assert (resp.content, idx) == ("ok", 0)
    rows = ledger()
    assert len(rows) == 1
    assert (rows[0]["service"], rows[0]["model"], rows[0]["caller"]) == (
        "google", config.GOOGLE_MODEL, "langHero:gemini"
    )
    assert (rows[0]["input_tokens"], rows[0]["output_tokens"]) == (9, 2)


def test_elevenlabs_books_one_row(ledger, monkeypatch, tmp_path):
    from voice import elevenlabs

    class FakeClient:
        text_to_speech = types.SimpleNamespace(convert=lambda **kw: iter([b"ab", b"cd"]))

    monkeypatch.setattr(elevenlabs, "get_client", lambda: FakeClient())
    monkeypatch.setattr(elevenlabs, "tts_cache_lookup", lambda *a, **k: None)
    monkeypatch.setattr(elevenlabs, "tts_cache_path", lambda *a, **k: str(tmp_path / "clip.mp3"))
    monkeypatch.setattr(elevenlabs, "tts_response", lambda f, *a: {"file": f})

    out = elevenlabs.synthesize_speech("你好", voice_id="voice123")
    assert (tmp_path / "clip.mp3").read_bytes() == b"abcd"
    assert out == {"file": str(tmp_path / "clip.mp3")}
    rows = ledger()
    assert len(rows) == 1
    assert (rows[0]["service"], rows[0]["model"], rows[0]["caller"]) == (
        "elevenlabs", "eleven_multilingual_v2", "langHero:elevenlabs_tts"
    )
    assert rows[0]["units"] == {"chars": 2, "voice_id": "voice123"}


def test_jev_books_one_row(ledger, monkeypatch):
    from lib import jev_client

    class FakeResp:
        status_code = 200
        text = ""

        def json(self):
            return {"answers": {"q": 0.5}, "model": "jev-2026-11"}

    monkeypatch.setattr(jev_client.requests, "post", lambda *a, **k: FakeResp())
    answers = jev_client.call(
        state={"unique": "ai_calls_test"}, questions={"q": {"type": "noul"}}, api_key="k",
        caller="practice_scoring",
    )
    assert answers == {"q": 0.5}
    rows = ledger()
    assert len(rows) == 1
    assert (rows[0]["service"], rows[0]["model"], rows[0]["caller"], rows[0]["calls"]) == (
        "jev", "jev-2026-11", "langHero:practice_scoring", 1
    )

    # A cache hit is not an AI call: still one row.
    jev_client.call(state={"unique": "ai_calls_test"}, questions={"q": {"type": "noul"}}, api_key="k")
    assert len(ledger()) == 1


def test_every_jev_call_site_names_its_caller():
    """No Jev call site may fall back to the default caller `jev_client` (the ledger would
    then book all Jev spend under one name)."""
    import ast
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    files = [p for p in (root / "backend").rglob("*.py")
             if "venv" not in p.parts and "__pycache__" not in p.parts]
    files.append(root / "tests" / "improvements" / "suite.py")
    client = root / "backend" / "lib" / "jev_client.py"

    sites, missing = 0, []
    for path in files:
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func
            is_jev = (isinstance(f, ast.Attribute) and f.attr == "call"
                      and isinstance(f.value, ast.Name) and f.value.id == "jev_client")
            is_jev = is_jev or (path == client and isinstance(f, ast.Name) and f.id == "call")
            if not is_jev:
                continue
            sites += 1
            kw = next((k for k in node.keywords if k.arg == "caller"), None)
            good = (kw is not None and isinstance(kw.value, ast.Constant)
                    and isinstance(kw.value.value, str) and kw.value.value
                    and ":" not in kw.value.value)
            if not good:
                missing.append(f"{path.relative_to(root)}:{node.lineno}")
    assert sites >= 6, f"found only {sites} Jev call sites; the scan is broken"
    assert not missing, f"Jev call sites without a bare caller= name: {missing}"


def test_failed_call_books_ok_false_and_reraises(ledger):
    with pytest.raises(ValueError):
        with ai_calls.track("openai", "gpt-x", "unit"):
            raise ValueError("provider down")
    rows = ledger()
    assert len(rows) == 1 and rows[0]["ok"] is False


def test_recorder_error_never_reaches_the_call(ledger, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("ledger broken")

    monkeypatch.setattr(ai_calls, "_ai_calls", types.SimpleNamespace(record=boom))
    with ai_calls.track("openai", "gpt-x", "unit") as t:
        t.response = "result"
    assert t.response == "result"

    monkeypatch.setattr(ai_calls, "_ai_calls", None)  # heroCommon not importable: no-op
    ai_calls.record("openai", "gpt-x", "unit")
    assert ledger() == []
