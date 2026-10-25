# Improvements test suite

A measurable gate. Every improvement proposed in the 3-track plan (Jev
findings · observability · UX) has a concrete, numeric pass criterion
captured as a test. The suite runs end-to-end against the live backend
and frontend, and prints a pass/fail dashboard.

**It is designed to fail now and turn green as improvements land.** The
pass count on the dashboard is the progress bar.

## Run

```
python3 tests/improvements/suite.py
```

Requires: `langhero-backend.service` live on :8100, `langhero-frontend.service`
live on :5200, `TYPESAFE_API_KEY` reachable (either env var or
`crankHero/.env`).

## Status categories

- **PASS** — the improvement is in place and the measured value meets the
  target.
- **FAIL** — the test ran but the measured value is below target. This is
  the normal state before an improvement lands.
- **SKIP** — the test needs infra that hasn't been built yet (e.g. the
  observability UI page). It is a FAIL in spirit but surfaced separately
  so you can tell "the thing exists but underperforms" from "the thing
  isn't built".

## Pass criteria per track

### Track 1 — Jev findings

| Test | Target |
|---|---|
| `jev_capability_drift` | All three baseline probes (register / timing / transition) within tolerance. |
| `jev_overconfirm_fixed` | ≤ 15% of recent tutor_lines match `[你您]是…吗？` AND avg naturalness ≥ 0.70. |
| `jev_level_signal_tight` | stdev(level_appropriate) across last 20 tutor_line rows ≤ 0.08. |
| `jev_setphrase_calibrated` | いらっしゃいませ / どうぞ召し上がれ / またお待ちしています each score ≥ 0.65 in context. |
| `jev_teaching_copy_skipped` | `time_freeze_lesson:2` not graded in last full pass. |

### Track 2 — Observability

| Test | Target |
|---|---|
| `obs_timeline_recorder_present` | `/story/journey_west` exposes `window.__langheroTimeline` with ≥ 3 event kinds. |
| `obs_sync_numbers_emit` | After one panel advance: audio-start delay recorded, typewriter/audio end delta recorded. |
| `obs_grades_ui_renders` | GET `/observability` returns 200 and page contains at least one grade row. |
| `obs_session_id_present` | Latest grade_log row has non-null `session_id` in state. |
| `obs_full_pass_cron` | `systemctl list-timers` shows `langhero-full-pass.timer`. |
| `obs_capability_cron` | Same for `langhero-capability.timer`. |
| `obs_jev_cache_hits` | Identical state+questions second call ≤ 10ms (cached). |

### Track 3 — UX

| Test | Target |
|---|---|
| `ux_catalog_cover_art` | Scenario story cards on `/catalog` render `<img>` with `cover_image` URL. |
| `ux_profile_page_exists` | GET `/profile` returns 200 and page contains "lives" and "score" labels. |
| `ux_progress_sync_endpoint` | POST then GET `/api/progress/{user}/{story}` round-trips the same JSON. |
| `ux_practice_no_autoselect` | GET `/practice` HTML does not auto-mount into chat view. |
| `ux_settings_menu_entry` | GET `/` HTML menu contains a "Settings" button. |
| `ux_audio_sync_within_bounds` | Measured audio-start delay ≤ 500 ms across 3 panel advances. |

## Baselines

`baselines.json` is captured by `suite.py --capture-baseline`. It snapshots
the current measured values so each test can compare against a frozen
reference point. Overwrite it only when a measurement methodology changes,
not when a value improves (the point is to prove improvement vs. baseline).

## Adding a new test

In `suite.py`, add a `@check("<category>", "<name>")` function returning
`CheckResult(status, actual, target, hint)`. The runner picks it up by
decorator; no registration needed.
