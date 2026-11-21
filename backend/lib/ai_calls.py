"""langHero's one seam to the hero AI-calls counter (heroCommon ``hero_common.ai_calls``).

Every AI request langHero makes (OpenAI chat / whisper / TTS / images, Gemini chat and images,
ElevenLabs voice, Jev) is booked here as one row: service, model, caller "langHero:<component>",
tokens when the response reports them, otherwise units (chars, images, audio bytes).

    from lib import ai_calls
    with ai_calls.track("openai", model, "story_generator") as t:
        t.response = client.chat.completions.create(...)

    ai_calls.record("elevenlabs", "eleven_multilingual_v2", "voice", units={"chars": 42})

``track`` books the row when the block ends, ``ok=False`` if it raised (the exception is
re-raised untouched). Recording never changes the call: without heroCommon importable (another
workspace) every function is a no-op, and any recorder error is swallowed. Tests point env
``AI_CALLS_LEDGER`` at a temp file (tests/conftest.py does it for the whole suite).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

CALLER_PREFIX = "langHero:"

try:
    from hero_common import ai_calls as _ai_calls
except Exception:  # not installed on this interpreter: try a sibling heroCommon checkout, else no-op
    try:
        _src = Path(__file__).resolve().parents[3] / "heroCommon" / "src"
        if _src.is_dir() and str(_src) not in sys.path:
            sys.path.append(str(_src))
        from hero_common import ai_calls as _ai_calls
    except Exception:
        _ai_calls = None


def record(
    service: str,
    model: str,
    component: str,
    *,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cost_usd: float | None = None,
    units: dict | None = None,
    ok: bool = True,
    calls: int = 1,
) -> None:
    """One row for one AI request (or ``calls`` attempts). Never raises."""
    if _ai_calls is None:
        return
    try:
        caller = component if ":" in component else CALLER_PREFIX + component
        _ai_calls.record(
            service,
            model or "unknown",
            caller=caller,
            calls=calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            units=units,
            ok=ok,
        )
    except Exception:
        pass


def _get(obj: Any, *names: str) -> Any:
    for name in names:
        val = obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)
        if val is not None:
            return val
    return None


def usage_tokens(resp: Any) -> tuple[int, int]:
    """(input, output) tokens from an OpenAI SDK, LangChain or Gemini REST response; (0, 0) if absent."""
    try:
        if resp is None or isinstance(resp, (str, bytes)):
            return 0, 0
        usage = _get(resp, "usage", "usage_metadata", "usageMetadata")
        if usage is None:
            return 0, 0
        tin = _get(usage, "prompt_tokens", "input_tokens", "promptTokenCount") or 0
        tout = _get(usage, "completion_tokens", "output_tokens", "candidatesTokenCount") or 0
        return int(tin), int(tout)
    except Exception:
        return 0, 0


class track:
    """Context manager booking one row when the block ends (sync or inside async code).

    Set ``.response`` to the provider response to pick up its token usage, or ``.input_tokens`` /
    ``.output_tokens`` / ``.units`` / ``.model`` directly. Never swallows the block's exception.
    """

    def __init__(self, service: str, model: str, component: str, units: dict | None = None):
        self.service = service
        self.model = model
        self.component = component
        self.units = units
        self.response: Any = None
        self.input_tokens = 0
        self.output_tokens = 0

    def __enter__(self) -> "track":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        try:
            tin, tout = usage_tokens(self.response)
            record(
                self.service,
                self.model,
                self.component,
                input_tokens=self.input_tokens or tin,
                output_tokens=self.output_tokens or tout,
                units=self.units,
                ok=exc_type is None,
            )
        except Exception:
            pass
        return False
