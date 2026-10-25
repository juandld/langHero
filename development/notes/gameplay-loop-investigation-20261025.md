# Investigation: main gameplay loop broken + ~20s response delay + Jev listening status

Date: 2026-10-25
Trigger: voice note from David — "Nellie is working on the main gameplay loop and
it's not working at all. Also there's a ~20s wait after recording. Did we ship
Jev listening?"

Scope: `langHero` (the `/play/*` and `/story/*` story-mode game — `GameView.svelte`
+ `/narrative/interaction`, `/narrative/imitate`, `/stream/interaction`). Backend
(`langhero-backend.service`) and frontend (`langhero-frontend.service`) were both
confirmed running throughout (no crash/outage — this is a logic/latency bug, not
downtime).

## 1. Why the main gameplay loop breaks ("not working at all")

**Root cause: a WebSocket race between a background partial-transcription task and
the finalize/close path, in `backend/streaming.py` + `backend/routes/streaming.py`.**

The game defaults to the *streaming* path (`frontend/src/lib/config.ts:98` —
`getStreamMode()` defaults to `'real'` unless overridden in `localStorage`), which
opens a WS to `/stream/interaction`. While the mic is open, `StreamingSession`
(`backend/streaming.py:256-302`) fires a new background `asyncio.Task` roughly
every 400ms to transcribe the growing audio buffer and `websocket.send_json()` a
`partial` event (`_maybe_emit_partial` / `_emit_partial`, lines 256-302). When the
user releases the Speak button, `routes/streaming.py:218` calls
`session.finalize(websocket)`, which does `self.partial_task.cancel()`
(`streaming.py:309-310`) — but `Task.cancel()` only takes effect at the task's next
`await` point. If a partial task is already inside `await websocket.send_json(...)`
when `finalize()` sends the `final` event and the route's `finally:` block then
calls `websocket.close()` (`routes/streaming.py:245-250`), the two coroutines are
writing to the same socket concurrently. Whichever one loses the race hits
uvicorn's ASGI state machine after the connection is already closed and raises:

```
RuntimeError: Unexpected ASGI message 'websocket.close', after sending
'websocket.close' or response already completed.
```

This is confirmed live, verbatim, in the running service's journal (not simulated):

```
$ journalctl -u langhero-backend.service --since "2026-10-23 00:00:00" | grep -A2 "Exception in ASGI"
Oct 24 21:04:09 ... ERROR:    Exception in ASGI application
Oct 24 21:04:09 ... RuntimeError: Unexpected ASGI message 'websocket.close', after sending 'websocket.close' or response already completed.
```
(recurred 5 times between 21:04–21:15 on 2026-10-24, i.e. the evening David/Nellie
were playing). Traced the exact raise site to
`backend/venv/lib/python3.12/site-packages/uvicorn/protocols/websockets/websockets_impl.py:342-344`.

Because the race happens in the *background* partial task — which `streaming.py`
never `await`s and never wraps in try/except — the exception isn't caught by the
route's own `except WebSocketDisconnect` / `finally` handling. It surfaces only as
a server-side log line. From the player's side, the practical effect is: the
`final` event (containing the score/life delta the frontend needs to clear the
"evaluating" state and advance the story — `GameView.svelte` `applyInteractionResult`,
line ~307) can be dropped if it loses the race, or the socket is torn down with the
turn half-sent. The frontend has **no timeout, no retry, and no reconnect** on this
path (`frontend/src/lib/game/streamingManager.js` — `connect()`/`close()` have no
watchdog at all), so the UI is left stuck showing the recorded turn with nothing
happening — this is what reads as "not working at all."

Secondary, compounding issue found in the same logs: repeated
`WARNING:streaming:[silence-check] Could not check audio energy: Decoding failed.
ffmpeg returned error code: 183` — `_audio_has_speech()` (`streaming.py:97-110`)
tries to decode the **partial, growing** webm buffer with `pydub`/ffmpeg on every
partial-emit cycle; a partial/incomplete webm container fails to decode by
design, so this check fails open every single partial tick during real play (it
`return True`s on exception — not silent-breaking by itself, but it's wasted
ffmpeg subprocess spawns stacking up every ~400ms during every recording, adding
CPU load on the 2-vCPU box exactly while the latency-sensitive transcription call
for the same session is trying to run in the same executor).

**Not the cause:** service uptime. `langhero-backend.service` has been running
continuously since 2026-10-22 (`systemctl status` confirms, no restarts logged),
and `langhero-frontend.service` since 2026-09-12. This is a live logic bug, not a
crashed/stopped service.

## 2. Why responses take ~20 seconds (measured, not estimated)

Hit the real, running backend directly (`127.0.0.1:8100`) with a real ffmpeg-generated
webm clip — no mocked endpoints, no `python -c` simulation:

```
$ ffmpeg -f lavfi -i "sine=frequency=440:duration=3" -c:a libopus /tmp/test_audio.webm
$ time curl -F "audio_file=@test_audio.webm" -F "current_scenario_id=1" \
       -F "lang=Japanese" -F "judge=0" http://127.0.0.1:8100/narrative/interaction
```

4 runs, same input, same running server: **5.69s, 7.72s, 5.08s, 6.69s** total.
`/api/practice/chat` (the newer Jev-scored endpoint, see §3): **8.86s**.

Backend log for one of the runs:
```
02:07:50  [transcribe] context=interaction order=['openai', 'gemini'] ...
02:07:51  [transcribe] OK provider=openai text='ご視聴ありがとうございました。'
02:07:56  POST /narrative/interaction  200 OK        <- 5s AFTER transcription returned
```

Transcription itself (Whisper via OpenAI, first in the `interaction` provider
order — `backend/config.py:88`) returns in ~1s. The other 4-7s happens *after*
transcription, inside `process_interaction()` (`backend/services/interaction.py`):
when no keyword/yes-no/fuzzy-similarity match is found against the scenario's
options (lines 170-270 — likely on any non-exact phrasing, which is the normal
case for a real learner), the code falls through to a **second, sequential LLM
call** — "Semantic choice via LLM" (`interaction.py:293-355`, `providers.invoke_google`)
— to ask Gemini/OpenAI to pick the best-matching option by number. So a single
turn in the main gameplay loop = **up to 2 full sequential LLM round-trips**
(STT, then semantic match), each with no cache, no per-call timeout, and (per
`providers.py:229-255`) its own internal multi-key retry loop that tries every
configured Google key in sequence before falling back to OpenAI.

That retry fan-out matters tonight specifically: the same log window shows a live
Gemini outage —
```
02:02:16  WARNING:narrative.providers:Gemini invoke failed on key_index=0:
          503 UNAVAILABLE. 'This model is currently experiencing high demand...'
```
— so on a bad night, a turn that would normally cost ~5-8s can cost a 503 retry
on top for *each* of the two LLM calls, which is consistent with Nellie's reported
~20s. The `perf_tracker.py` module committed on 2026-07-09 (`81d0a2f feat(backend):
perf_tracker — per-endpoint latency ring buffer (not yet wired to /api/perf)`) was
built to record exactly this breakdown per-route, but **it is still not
wired to anything** — confirmed by `grep -rn "perf_tracker\|/api/perf" backend`
returning only the module's own file. No middleware calls `perf_tracker.record()`,
and there is no `/api/perf` route. So today this latency is invisible in-app; the
only way to see it is to read raw journal logs (as above) or re-run the curl
reproduction above.

## 3. Jev listening feature — status

**Jev scoring is implemented and verified live working — but only for a separate,
text-only practice screen, not for the spoken main gameplay loop.**

Verified end-to-end against the real running server:
```
$ curl -X POST http://127.0.0.1:8100/api/practice/chat -H "Content-Type: application/json" \
    -d '{"target_language":"Mandarin Chinese","history":[],"user_message":"你好",
         "user_intent":"greeting","scenario":"Order a beer in Beijing"}'
{"tutor_turn":"您好，喝点儿什么？",
 "scores":{"grammatical":0.98,"natural":0.8,"register":0.61,"meaning":0.93},
 "alternative":"您好。"}
```
(8.86s wall time — real calibrated Jev scores, not placeholders.) This is
`backend/routes/practice.py`, shipped in `3a5f0a5 feat(practice): TDD scaffold for
/practice v1c — Jev-scored live conversation` (2026-10-?? — one commit before the
most recent HEAD). It calls `practice_scoring.score_utterance()` →
`lib/jev_helpers.py` → `lib/jev_client.py` → the real Jev API, on four calibrated
0-1 dimensions (grammatical/natural/register/meaning), and separately
*log-only* grades the tutor's own reply (`jev_helpers.grade_tutor_line`,
`routes/practice.py:136-142`) without gating the response.

Two gaps between this and what David asked about ("more interactive experience" /
"listening"):

1. **It's text-only, not listening.** `frontend/src/routes/practice/+page.svelte`
   has a `<textarea>` (line 172) and no `MediaRecorder`/mic code at all — confirmed
   by grepping the file for `mic|audio|recorder|MediaRecorder`, zero hits outside
   the textarea. The learner types a sentence; Jev grades the typed text. There is
   no "Jev listens to your spoken Chinese" capability anywhere in the codebase.
2. **It's not wired into the main gameplay loop.** `grep -rln "jev" services/*.py
   streaming.py streaming_vocab.py routes/narrative.py` returns nothing — the
   actual story-mode speaking game (`GameView.svelte` → `/narrative/interaction` /
   `/narrative/imitate` / `/stream/interaction`) still uses the pre-Jev
   keyword-matching + fuzzy-similarity + "semantic choice LLM" pipeline described
   in §2. `/practice` is also not linked from the main nav/menu
   (`grep -rn "href=\"/practice\"" frontend/src/routes/+layout.svelte
   frontend/src/routes/menu/+page.svelte` → no matches) — it's a standalone route
   only reachable by typing the URL directly, so it isn't part of what Nellie is
   actually playing.

**Bottom line on Jev:** the grading engine works and is live; "Jev listening" as
an interactive *spoken* experience inside the game Nellie plays does not exist yet
— what shipped is a disconnected, unlinked, typing-based prototype.

## Fix candidates (not yet implemented — investigation only, per task scope)

1. `streaming.py::finalize()` — await/guard the cancelled `partial_task` (e.g.
   `await asyncio.gather(self.partial_task, return_exceptions=True)` before
   sending the final event and before the route's `websocket.close()`) so the two
   writers can't race the same socket.
2. `routes/streaming.py` — add a client-visible error event + `streamingManager.js`
   — add a connect/response timeout + one reconnect attempt, so a dropped final
   event degrades to a retry instead of a silent hang.
3. `services/interaction.py` — the "semantic choice via LLM" fallback
   (`interaction.py:293-355`) is the single biggest avoidable latency source; worth
   either caching per-(scenario, option-set) or giving it a hard per-call timeout
   with graceful degrade to the existing fuzzy-match result.
4. Wire `perf_tracker.record()` into actual request paths + add `/api/perf`, so
   this class of regression is visible without reading raw journal logs next time.
5. Decide whether Jev-scored *speech* is actually wanted in the main loop; if so,
   it needs a real voice input added to `/practice` (or Jev scoring added to
   `/narrative/interaction`), plus a nav link — today neither exists.
