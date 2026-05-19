"""
Provider utilities: Gemini (Google) and OpenAI fallbacks via LangChain.

Encapsulates key rotation, retry strategy decisions, and simple helpers for
transcription and title generation. Keeping this here makes services.py smaller
and easier to scan.
"""

from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

import config

# Initialize module logger early (before any usage)
logger = logging.getLogger("narrative.providers")

# Re-export OpenAI functions so callers can keep using `providers.romanize()` etc.
from providers_openai import (  # noqa: E402,F401
    title_with_openai,
    openai_chat,
    normalize_title_output,
    transcribe_with_openai,
    tts_with_openai,
    translate_text,
    romanize,
    makes_sense,
)


# Initialize Gemini clients (one per API key) for rotation
GOOGLE_KEYS = config.collect_google_api_keys()
GOOGLE_LLMS: List[ChatGoogleGenerativeAI] = [
    ChatGoogleGenerativeAI(model=config.GOOGLE_MODEL, api_key=k) for k in GOOGLE_KEYS
]

# Log configured model and key status for visibility
logger.info(
    "Gemini configured: model=%s, keys=%s",
    config.GOOGLE_MODEL,
    len(GOOGLE_KEYS),
)


def is_rate_limit_error(e: Exception) -> bool:
    s = str(e).lower()
    return (
        "429" in s
        or "rate limit" in s
        or "quota" in s
        or "exceeded your current quota" in s
    )


def key_label_from_index(index: int, keys: Optional[List[str]] = None) -> str:
    keys = keys if keys is not None else GOOGLE_KEYS
    try:
        key = keys[index]
    except Exception:
        return f"gemini_key_{index}"
    return f"gemini_key_{index}_{key[-4:] if key else '????'}"


@dataclass
class TranscriptionResult:
    text: str
    provider: str
    model: str
    meta: Dict[str, Any] = field(default_factory=dict)


# Transcription contexts
CONTEXT_INTERACTION = "interaction"
CONTEXT_STREAMING = "streaming"
CONTEXT_TRANSLATE = "translate"
CONTEXT_IMITATE = "imitate"
CONTEXT_NOTES = "notes"

_ALL_CONTEXTS = {
    CONTEXT_INTERACTION,
    CONTEXT_STREAMING,
    CONTEXT_TRANSLATE,
    CONTEXT_IMITATE,
    CONTEXT_NOTES,
}


def _available_providers() -> List[str]:
    providers: List[str] = []
    if GOOGLE_KEYS:
        providers.append("gemini")
    if config.OPENAI_API_KEY:
        providers.append("openai")
    return providers


def _expand_provider_order(prefs: List[str]) -> List[str]:
    order: List[str] = []
    available = _available_providers()
    if not available:
        return order
    tokens = prefs or ["auto"]
    for token in tokens:
        if token == "auto":
            for prov in available:
                if prov not in order:
                    order.append(prov)
            continue
        if token in available and token not in order:
            order.append(token)
    if not order:
        order.extend(available)
    return order


def _provider_order_for_context(context: str) -> List[str]:
    prefs = config.TRANSCRIBE_PROVIDER_OVERRIDES.get(context) or []
    if not prefs:
        prefs = config.TRANSCRIBE_PROVIDER_DEFAULT
    order = _expand_provider_order(prefs)
    if not order:
        raise RuntimeError("No transcription providers available. Configure API keys or provider preferences.")
    return order


def _mime_from_ext(file_ext: str) -> str:
    ext = (file_ext or "").lower()
    return {
        "webm": "audio/webm",
        "ogg": "audio/ogg",
        "mp3": "audio/mp3",
        "m4a": "audio/mp4",
        "wav": "audio/wav",
    }.get(ext, "audio/wav")


def _transcribe_with_gemini(
    audio_bytes: bytes,
    instructions: str,
    mime_type: str,
    model: Optional[str] = None,
) -> TranscriptionResult:
    message = HumanMessage(
        content=[
            {"type": "text", "text": instructions},
            {
                "type": "file",
                "source_type": "base64",
                "mime_type": mime_type,
                "data": b64encode(audio_bytes).decode("utf-8"),
            },
        ]
    )
    response, key_index = invoke_google([message], model=model)
    text = str(getattr(response, "content", response))
    return TranscriptionResult(
        text=text,
        provider="gemini",
        model=model or config.GOOGLE_MODEL,
        meta={"key_index": key_index},
    )


def _transcribe_with_openai_result(
    audio_bytes: bytes,
    file_ext: str,
    language: Optional[str],
    prompt: Optional[str],
) -> TranscriptionResult:
    text = transcribe_with_openai(audio_bytes, file_ext=file_ext, language=language, prompt=prompt)
    return TranscriptionResult(
        text=text,
        provider="openai",
        model=config.OPENAI_TRANSCRIBE_MODEL,
    )


def transcribe_audio(
    audio_bytes: bytes,
    *,
    file_ext: str = "webm",
    mime_type: Optional[str] = None,
    instructions: Optional[str] = None,
    language_hint: Optional[str] = None,
    context: str = CONTEXT_INTERACTION,
) -> TranscriptionResult:
    if context not in _ALL_CONTEXTS:
        # Allow custom contexts but treat as default
        order = _expand_provider_order(config.TRANSCRIBE_PROVIDER_DEFAULT)
    else:
        order = _provider_order_for_context(context)
    if not order:
        raise RuntimeError("No transcription providers configured.")
    instruction_text = instructions or "Transcribe this audio recording."
    mime = mime_type or _mime_from_ext(file_ext)
    logger.info("[transcribe] context=%s order=%s bytes=%d lang_hint=%s", context, order, len(audio_bytes), language_hint)
    last_err: Optional[Exception] = None
    for provider_name in order:
        try:
            if provider_name == "gemini":
                result = _transcribe_with_gemini(audio_bytes, instruction_text, mime)
                logger.info("[transcribe] OK provider=gemini key=%s text=%r", result.meta.get("key_index"), (result.text or "")[:100])
                return result
            if provider_name == "openai":
                result = _transcribe_with_openai_result(
                    audio_bytes,
                    file_ext=file_ext,
                    language=language_hint,
                    prompt=instruction_text if instruction_text else None,
                )
                logger.info("[transcribe] OK provider=openai text=%r", (result.text or "")[:100])
                return result
            raise RuntimeError(f"Unsupported transcription provider '{provider_name}'")
        except Exception as exc:  # noqa: PERF203
            last_err = exc
            logger.warning("Transcription via %s failed: %s", provider_name, exc)
            continue
    if last_err:
        raise last_err
    raise RuntimeError("No transcription providers succeeded.")


def invoke_google(messages: List[HumanMessage], model: str | None = None) -> Tuple[object, int]:
    """Try Gemini clients in order (no internal retries). Returns (response, key_index).

    If `model` is provided, use a transient set of clients for that model.
    """
    last_err: Optional[Exception] = None
    llms: List[ChatGoogleGenerativeAI]
    if model and model != config.GOOGLE_MODEL:
        # Build a temporary rotation with the requested model
        llms = [ChatGoogleGenerativeAI(model=model, api_key=k) for k in GOOGLE_KEYS]
    else:
        llms = GOOGLE_LLMS
    for idx, llm in enumerate(llms):
        try:
            # Disable internal retries by overriding keyword
            resp = llm.invoke(messages, max_retries=0)
            logger.info("[invoke_google] OK key_index=%d/%d", idx, len(llms))
            return resp, idx
        except Exception as e:
            last_err = e
            logger.warning(
                "Gemini invoke failed on key_index=%s: %s", idx, str(e)
            )
            continue
    if last_err:
        raise last_err
    raise RuntimeError("No Google Gemini API keys configured.")


