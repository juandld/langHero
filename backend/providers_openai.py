"""OpenAI provider functions: transcription, TTS, translation, romanization.

Extracted from providers.py to keep each module under ~300 lines.
All functions are re-exported from providers.py for backward compatibility.
"""
from __future__ import annotations

import io
import logging
from typing import Optional

from langchain_openai import ChatOpenAI

import config

logger = logging.getLogger("narrative.providers")


def title_with_openai(text: str) -> str:
    """Generate a short title via OpenAI (LangChain)."""
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OpenAI fallback not configured.")
    llm = ChatOpenAI(model=config.OPENAI_TITLE_MODEL, api_key=config.OPENAI_API_KEY, temperature=0.3)
    prompt = (
        "Return exactly one short title (5–8 words) for the transcription below. "
        "Use the same language as the transcription. Do not include quotes, bullets, markdown, or any extra text. "
        "Output only the title on a single line.\n\n" + text
    )
    resp = llm.invoke(prompt)
    raw = str(getattr(resp, "content", resp))
    return normalize_title_output(raw)


def openai_chat(messages: list, model: str | None = None, temperature: float = 0.2) -> str:
    """Generic OpenAI chat wrapper returning content text."""
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OpenAI fallback not configured.")
    use_model = model or config.OPENAI_NARRATIVE_MODEL
    llm = ChatOpenAI(model=use_model, api_key=config.OPENAI_API_KEY, temperature=temperature)
    resp = llm.invoke(messages)
    return str(getattr(resp, "content", resp))


def normalize_title_output(raw: str) -> str:
    """Coerce LLM output into a single, clean title line.

    - Removes markdown (bullets, bold/italics) and boilerplate prefaces
    - Picks the first plausible title line
    - Trims excessive punctuation and length
    """
    try:
        text = (raw or "").strip()
        if not text:
            return "Untitled"
        # Remove obvious prefaces
        lower = text.lower()
        if "here are" in lower and ":" in text:
            text = text.split(":", 1)[-1].strip()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        candidates = []
        for line in lines:
            if line.endswith(":"):
                continue
            l = line
            for prefix in ("- ", "* ", "• ", "1. ", "2. ", "3. ", "-", "*", "•"):
                if l.startswith(prefix):
                    l = l[len(prefix):].strip()
            l = l.replace("**", "").replace("__", "").replace("*", "").replace("_", "").strip()
            if l:
                candidates.append(l)
        if not candidates:
            candidates = [text]
        title = candidates[0]
        for sep in [" • ", " | ", ";", "  -  ", "  *  "]:
            if sep in title:
                title = title.split(sep, 1)[0].strip()
        title = title.strip().strip('"').strip("'")
        while title and title[-1] in [".", ":", "-", "|", ";"]:
            title = title[:-1].rstrip()
        if len(title) > 80:
            parts = title.split()
            out = []
            for p in parts:
                if len(" ".join(out + [p])) <= 80:
                    out.append(p)
                else:
                    break
            if out:
                title = " ".join(out)
        return title or "Untitled"
    except Exception:
        return "Untitled"


def transcribe_with_openai(
    audio_bytes: bytes,
    file_ext: str = "wav",
    language: Optional[str] = None,
    prompt: Optional[str] = None,
) -> str:
    """Transcribe audio using OpenAI Whisper via the official SDK."""
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OpenAI fallback not configured.")
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    bio = io.BytesIO(audio_bytes)
    bio.name = f"audio.{file_ext}"
    kwargs = {
        "model": config.OPENAI_TRANSCRIBE_MODEL,
        "file": bio,
        "response_format": "text",
        "temperature": 0,
    }
    hint = (language or "").strip()
    _lang_to_iso = {
        "japanese": "ja", "english": "en", "spanish": "es",
        "ja": "ja", "en": "en", "es": "es",
    }
    iso_code = _lang_to_iso.get(hint.lower()) if hint else None
    if iso_code:
        kwargs["language"] = iso_code
    if prompt:
        kwargs["prompt"] = prompt
    elif hint:
        kwargs["prompt"] = (
            f"The speaker may be using {hint}. Transcribe in the language actually spoken using its usual writing system. "
            "Do not translate."
        )
    resp = client.audio.transcriptions.create(**kwargs)
    return resp if isinstance(resp, str) else getattr(resp, "text", "")


def tts_with_openai(
    text: str,
    voice: str = "alloy",
    fmt: str = "mp3",
    instructions: str | None = None,
) -> bytes:
    """Synthesize speech for a short phrase using OpenAI TTS."""
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OpenAI TTS not configured.")
    from openai import OpenAI
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    model = config.OPENAI_TTS_MODEL

    kwargs = {
        "model": model,
        "voice": voice,
        "input": text,
    }

    if instructions and "gpt-4o" in model:
        kwargs["instructions"] = instructions

    try:
        resp = client.audio.speech.create(**kwargs, format=fmt)
        data = getattr(resp, "content", None)
        if data is None and hasattr(resp, "read"):
            data = resp.read()
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
    except Exception:
        try:
            resp = client.audio.speech.create(**kwargs)
            data = getattr(resp, "content", None)
            if isinstance(data, (bytes, bytearray)):
                return bytes(data)
        except Exception as e:
            raise e
    raise RuntimeError("TTS synthesis failed.")


def translate_text(text: str, to_language: str, from_language: str | None = None) -> str:
    """Translate short text into the requested language using OpenAI chat."""
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OpenAI translation not configured.")
    llm = ChatOpenAI(model=config.OPENAI_TITLE_MODEL, api_key=config.OPENAI_API_KEY, temperature=0.0)
    prompt = (
        (f"Translate this phrase from {from_language} to {to_language}:\n" if from_language else f"Translate this phrase into {to_language}:\n")
        + text
        + "\nReturn only the translation, no quotes, no notes."
    )
    resp = llm.invoke(prompt)
    return str(getattr(resp, "content", resp)).strip().strip('"').strip("'")


def romanize(text: str, language: str) -> str:
    """Return a simple pronunciation/romanization line for the target language."""
    if not text:
        return ""
    lang = (language or "").strip().lower()
    if "japanese" in lang or "ja" == lang:
        if not config.OPENAI_API_KEY:
            return ""
        llm = ChatOpenAI(model=config.OPENAI_TITLE_MODEL, api_key=config.OPENAI_API_KEY, temperature=0.0)
        prompt = (
            "Provide romaji for this Japanese phrase. Return only the romaji, no quotes or notes.\n" + text
        )
        try:
            resp = llm.invoke(prompt)
            return str(getattr(resp, "content", resp)).strip().strip('"').strip("'")
        except Exception:
            return ""
    return ""


def makes_sense(text: str, language: str | None = None) -> bool:
    """Classify whether the text is a simple, coherent utterance in the given language."""
    try:
        if not text:
            return False
        if not config.OPENAI_API_KEY:
            return bool(text.strip())
        llm = ChatOpenAI(model=config.OPENAI_TITLE_MODEL, api_key=config.OPENAI_API_KEY, temperature=0.0)
        lang = (language or "").strip() or "the target language"
        prompt = (
            f"Answer yes or no: Is this a short, coherent, appropriate utterance in {lang}?\n"
            f"Text: {text}\n"
            "Answer strictly 'yes' or 'no'."
        )
        resp = llm.invoke(prompt)
        out = str(getattr(resp, "content", resp)).strip().lower()
        return out.startswith('y')
    except Exception:
        return False
