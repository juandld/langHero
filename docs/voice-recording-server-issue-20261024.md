# Voice recording server issue — investigation & fix (2026-10-24)

## Report

David: *"When I try to record my answer, it has a problem with the server. I can't
send my voice recording answer to the questions."* (voice note, session
7a4230ad, 2026-10-24 21:02:22Z)

## Root cause

`backend/routes/streaming.py`, `interaction_stream_endpoint` (the `/stream/interaction`
WebSocket used by every "speak your answer" game round), had an unconditional
`finally: await websocket.close()` after its receive loop. Whenever the loop exited
via the `websocket.disconnect` branch — i.e. the **client** closed the socket first
(scenario change, component teardown, Vite HMR reload, cancel, tab close — anything
that doesn't send a `stop`/`finish` text frame before closing) — the server tried to
send a second WebSocket close frame on a connection ASGI had already torn down.
Uvicorn rejects that as a protocol violation and raises, which FastAPI turns into an
unhandled 500-style ASGI exception for that connection. The frontend sees the socket
die with no `final` event, so the recorded answer is lost — exactly the symptom
reported.

`/stream/mock` (`mock_stream_endpoint`) had the identical pattern (unconditional
`send_json` + `close()` after the loop, regardless of disconnect vs. normal exit) and
was fixed the same way, though it isn't the endpoint real recordings use.

## Evidence (measured, not estimated)

- `journalctl -u langhero-backend.service --since "14 days ago"`: **8** `WebSocket
  /stream/interaction [accepted]` connections logged, **5** of them (**62.5%**)
  immediately followed by:
  ```
  RuntimeError: Unexpected ASGI message 'websocket.close', after sending
  'websocket.close' or response already completed.
  ```
  at `routes/streaming.py:244` (`await websocket.close()` in the `finally` block).
  Occurrences: Oct 20 21:47:04, Oct 20 21:47:36, Oct 24 21:04:09 (×2 — the two
  connections opened right as David recorded the voice note at 21:02:22Z, two
  minutes earlier, reporting the exact same problem).
- **Live reproduction** against the running server (`ws://127.0.0.1:8100/stream/interaction`,
  PID 2713709, pre-fix): connect → send init JSON → send a text frame → close the
  socket client-side (mirrors `frontend/src/lib/game/streamingManager.js`'s own
  `close()`, which does exactly this) → **same traceback, same line, reproduced on
  demand** (`/tmp/repro_ws_close.py`).
- **Post-fix reproduction**, same script, against reloaded server (new PID 2721775):
  clean `connection open` → `connection closed`, no exception.
- **Regression check**: normal flow (init → audio bytes → `stop` text) still completes
  `FINALIZE` and sends the `final` event before closing cleanly, both before and after
  the fix (`/tmp/repro_ws_happy.py`).

## Fix

`backend/routes/streaming.py`:
- Import `starlette.websockets.WebSocketState`.
- `interaction_stream_endpoint`: in the `finally` block, only call `websocket.close()`
  if `websocket.client_state != WebSocketState.DISCONNECTED`; wrapped in
  `try/except RuntimeError` as a defensive second layer against the same race.
- `mock_stream_endpoint`: same `client_state` guard before the trailing
  `send_json`/`close()`.

Picked up automatically by the `--reload` uvicorn dev server (`langhero-backend.service`);
no rebuild/restart needed. Verified live per the reproductions above.

## Pre-existing, unrelated

`tests/streaming_interaction_test.py::test_streaming_interaction_flow` fails both
before and after this fix (`assert 'penalty' == 'final'` — an extra `penalty` event
arrives before `final` in that mocked scenario path). Confirmed via `git stash` that
this failure predates this change; out of scope for this task.
