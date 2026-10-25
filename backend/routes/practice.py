"""Live-conversation practice endpoint: LLM tutor turn + Jev scoring.

v1c — learner types a response to a scenario character, Jev scores the
utterance on 4 calibrated dims, and the LLM tutor's next line reacts to
both the conversation and the scores (e.g. acts confused if register
was off). Streaming can come later; this returns synchronously.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

import providers
from lib import jev_helpers
from practice_scoring import mock_enabled, score_utterance

router = APIRouter(prefix="/api/practice", tags=["practice"])

SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "scenarios" / "practice"


class HistoryTurn(BaseModel):
    role: Literal["tutor", "learner"]
    text: str
    translation: Optional[str] = None


class PracticeChatRequest(BaseModel):
    target_language: str
    history: list[HistoryTurn] = []
    user_message: str
    user_intent: str
    scenario: str
    learner_level: Optional[str] = None
    session_id: Optional[str] = None


class Scores(BaseModel):
    grammatical: float
    natural: float
    register: float
    meaning: float


class PracticeChatResponse(BaseModel):
    tutor_turn: str
    scores: Scores
    alternative: str


def _tutor_prompt(req: PracticeChatRequest, scores: dict) -> str:
    # Jev only grades (calibrated 0..1 noul questions); it cannot generate text.
    # So the native-speaker "alternative" rewrite is produced here, by the same
    # LLM call that generates the tutor's next line.
    history_lines = "\n".join(f"{turn.role}: {turn.text}" for turn in req.history) or "(no prior turns)"
    return (
        f"You are a native {req.target_language} speaker playing a character in this "
        f"scenario: {req.scenario}\n\n"
        f"Conversation so far:\n{history_lines}\n\n"
        f"The learner just said: {req.user_message}\n"
        f"(Learner's intended meaning: {req.user_intent})\n\n"
        "An automatic grader scored the learner's utterance on 0..1 scales: "
        f"grammatical={scores['grammatical']:.2f}, natural={scores['natural']:.2f}, "
        f"register={scores['register']:.2f}, meaning={scores['meaning']:.2f}.\n\n"
        "Respond with EXACTLY two lines, no other text:\n"
        f"TUTOR: <your next line of dialogue in character, in {req.target_language}, "
        "one or two short sentences. Respond DIRECTLY as a native speaker would — "
        "serve the order, answer the question, continue the exchange. Do NOT ask "
        "echo-confirmation questions like '你是…吗？' / '您是…吗？' when the learner's "
        "intent is clear. Only ask a brief clarifying question when the input is "
        "genuinely ambiguous. If register or natural scored low, react naturally "
        "(mild confusion is fine) instead of over-politely confirming.>\n"
        f"ALTERNATIVE: <a natural, native-speaker way to say what the learner meant, in "
        f"{req.target_language}. Leave this blank if the learner's phrasing was already "
        "native-quality.>"
    )


def _parse_tutor_response(text: str) -> tuple[str, str]:
    tutor_match = re.search(r"TUTOR:\s*(.*?)(?:\n\s*ALTERNATIVE:|$)", text, re.DOTALL)
    alt_match = re.search(r"ALTERNATIVE:\s*(.*)", text, re.DOTALL)
    tutor_turn = tutor_match.group(1).strip() if tutor_match else text.strip()
    # An explicit "ALTERNATIVE:" marker with nothing after it is the LLM
    # deliberately signalling native-quality phrasing — keep that "".
    # A missing marker means the response didn't follow the format at all,
    # so don't assert native-quality by defaulting to "" — surface the raw
    # text instead.
    alternative = alt_match.group(1).strip() if alt_match else text.strip()
    return tutor_turn, alternative


@router.get("/scenarios")
async def practice_scenarios() -> list[dict]:
    if not SCENARIOS_DIR.is_dir():
        return []
    scenarios = [json.loads(p.read_text()) for p in SCENARIOS_DIR.glob("*.json")]
    scenarios.sort(key=lambda s: s["id"])
    return scenarios


@router.post("/chat", response_model=PracticeChatResponse)
async def practice_chat(req: PracticeChatRequest) -> PracticeChatResponse:
    scores = score_utterance(
        target_language=req.target_language,
        scenario=req.scenario,
        history=[turn.model_dump() for turn in req.history],
        user_intent=req.user_intent,
        utterance=req.user_message,
    )

    if mock_enabled():
        # Skip the LLM call too — it's the actual bottleneck (10s+), not Jev,
        # and the E2E test needs scores rendered within 5s.
        tutor_turn = "（模拟）好的。"
        alternative = ""
    else:
        prompt = _tutor_prompt(req, scores)
        try:
            resp, _key_index = providers.invoke_google([HumanMessage(content=[{"type": "text", "text": prompt}])])
            raw = str(getattr(resp, "content", resp)).strip()
        except Exception:
            raw = str(providers.openai_chat([HumanMessage(content=prompt)])).strip()

        tutor_turn, alternative = _parse_tutor_response(raw)

        # Log-only grading of the tutor's own line — catches cases like the
        # tutor using an archaic register at a casual scene. Never gates the
        # response; a Jev outage returns {} and the practice route is unaffected.
        jev_helpers.grade_tutor_line(
            scenario=req.scenario,
            target_language=req.target_language,
            tutor_line=tutor_turn,
            learner_level=req.learner_level,
            session_id=req.session_id,
        )

    return PracticeChatResponse(tutor_turn=tutor_turn, scores=Scores(**scores), alternative=alternative)
