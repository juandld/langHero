"""Full observability pass over all gradable content in the repo.

Runs:
  (a) 3 practice scenarios × 3 turns via /api/practice/chat
      → 9 fresh tutor_line grades (same path as live users)
  (b) Every CJK-containing dialogue line NOT tagged kind=teaching_copy
      → dialogue_script grades
  (c) Every legacy narrative scene's character dialogue
      → legacy_scene grades

All grades land in backend/storage/grades.sqlite. Designed to run on a nightly
systemd timer and compare vs. the previous night.

Run manually:
    python3 backend/scripts/full_content_pass.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import uuid
from pathlib import Path

import requests

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
from lib import jev_helpers  # noqa: E402

BACKEND = "http://127.0.0.1:8100"
SCENARIO_DIR = BACKEND_DIR / "scenarios" / "practice"


# ---------- (a) practice scenarios ----------

PRACTICE_CONVERSATIONS = {
    "beijing-bar-order-a-beer": [
        ("一瓶啤酒", "I want to order one bottle of beer"),
        ("青岛就好", "Qingdao brand is fine"),
        ("多少钱?", "How much does it cost?"),
    ],
    "cafe-order-a-coffee": [
        ("我要一杯拿铁", "I want to order a latte"),
        ("大杯的,谢谢", "Large size, please"),
        ("带走", "Takeaway, not for here"),
    ],
    "taxi-tell-driver-destination": [
        ("去北京首都机场", "Please take me to Beijing Capital Airport"),
        ("T2航站楼", "Terminal 2 specifically"),
        ("大概多久?", "About how long will it take?"),
    ],
}


def run_practice() -> int:
    n = 0
    session_id = str(uuid.uuid4())
    for sid, turns in PRACTICE_CONVERSATIONS.items():
        scen = json.loads((SCENARIO_DIR / f"{sid}.json").read_text())
        history = [{"role": t["role"], "text": t["text"], "translation": t.get("translation")}
                   for t in scen.get("starter_turns", [])]
        for msg, intent in turns:
            resp = requests.post(
                f"{BACKEND}/api/practice/chat",
                json={
                    "target_language": scen["target_language"],
                    "history": history,
                    "user_message": msg,
                    "user_intent": intent,
                    "scenario": f"{scen['description']} (register: {scen.get('register', 'unspecified')})",
                    "learner_level": "A2",
                    "session_id": session_id,
                },
                timeout=90,
            )
            if resp.status_code != 200:
                print(f"  practice {sid} failed: {resp.status_code}", file=sys.stderr)
                break
            body = resp.json()
            history.append({"role": "learner", "text": msg})
            history.append({"role": "tutor", "text": body["tutor_turn"]})
            n += 1
            print(f"  practice {sid}: tutor='{body['tutor_turn'][:30]}' ok")
    return n


# ---------- (b) dialogue scripts ----------

def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[぀-ゟ゠-ヿ㐀-䶿一-鿿]", text))


def run_dialogues() -> int:
    with (BACKEND_DIR / "stories.json").open() as f:
        data = json.load(f)
    dialogues = data.get("dialogues", {})

    graded_lines: set[tuple[str, int, str]] = set()
    n = 0
    skipped_teaching = 0
    for script_key, lines in dialogues.items():
        for i, line in enumerate(lines):
            text = line.get("text", "")
            if not _has_cjk(text):
                continue
            if line.get("kind") == "teaching_copy":
                skipped_teaching += 1
                continue
            dedup_key = (script_key, i, text)
            if dedup_key in graded_lines:
                continue
            graded_lines.add(dedup_key)
            if re.search(r"[぀-ゟ゠-ヿ]", text):
                story_lang = "Japanese"
            elif script_key.startswith("hk_"):
                story_lang = "Mandarin Chinese"
            else:
                story_lang = "Mandarin Chinese"
            jev_helpers.grade_authored_line(
                scenario=f"Dialogue script '{script_key}' — {line.get('sentiment', '')} line from {line.get('speaker', 'character')}.",
                target_language=story_lang,
                line=text,
                grader_name="dialogue_script",
                speaker=line.get("speaker"),
                source_id=f"{script_key}:{i}",
            )
            n += 1
            print(f"  dialogue {script_key}:{i} '{text[:30]}' ok")
    if skipped_teaching:
        print(f"  (skipped {skipped_teaching} lines tagged kind=teaching_copy)")
    return n


# ---------- (c) legacy scenes ----------

def run_legacy() -> int:
    with (BACKEND_DIR / "scenarios.json").open() as f:
        scens = json.load(f)
    n = 0
    for s in scens:
        sid = s["id"]
        line = s.get("character_dialogue_jp") or s.get("character_dialogue_zh") or s.get("character_dialogue_mandarin")
        if not line:
            continue
        if s.get("character_dialogue_zh"):
            lang = "Mandarin Chinese"
        else:
            lang = "Japanese"
        jev_helpers.grade_authored_line(
            scenario=f"{s.get('setting', '')} — {s.get('description', '')}",
            target_language=lang,
            line=line,
            grader_name="legacy_scene",
            source_id=f"legacy:{sid}",
        )
        n += 1
        print(f"  legacy {sid} '{line[:30]}' ok")
    return n


if __name__ == "__main__":
    t0 = time.time()
    print("=== (a) practice scenarios ===")
    a = run_practice()
    print(f"  → {a} practice tutor-lines graded\n")

    print("=== (b) dialogue scripts ===")
    b = run_dialogues()
    print(f"  → {b} dialogue script lines graded\n")

    print("=== (c) legacy narrative scenes ===")
    c = run_legacy()
    print(f"  → {c} legacy scenes graded\n")

    print(f"TOTAL: {a + b + c} new grades written in {time.time()-t0:.1f}s")
