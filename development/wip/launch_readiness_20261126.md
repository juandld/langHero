# LangHero launch readiness: what stands between today's app and a first paying user (2026-11-26)

David, 2026-11-26: "we are going to need an extra source of income soon". Product rule so far
(`development/decision-board.md:70-78`, D4): the free tier is the marketing loop with heavy reuse and caching;
**paid unlocks story import and generation**; tier knobs (quotas per day) are still open.

Everything below was checked against the running app on 2026-11-26 around 03:10Z (backend `127.0.0.1:8100`,
frontend `127.0.0.1:5200`) and the code at `293ceb9`. No code, config or Cloudflare setting was changed. One live
story import was run (one Gemini call, $0.009) to prove MVP bullet 1.

## 1. MVP definition, line by line (`development/north-star-execution.md:21-28`)

| # | MVP bullet | Verdict | Evidence |
|---|---|---|---|
| 1 | A user can import a story seed (text v0) and immediately play a scenario chain | **Done** | Live call: `curl -X POST 127.0.0.1:8100/api/stories/import -d '{"text":"A traveler arrives at a noodle stall in Taipei at midnight. ...","target_language":"Mandarin","max_scenes":3,"activate":false,"attest_rights":true}'` returned `target_language: "Mandarin Chinese"` and 3 scenes (`1 beginner lives=3 options=3`, `2 advanced lives=2 options=2`, `3 beginner lives=3 options=0`). Ledger row `2026-11-26T03:12:29 langHero:gemini gemini-2.5-flash 278 in / 3563 out`. Route: `backend/routes/import_routes.py:117`; it needs `attest_rights:true` (`:120`), without it the call returns `{"detail":"attest_rights_required"}`. Frontend route `frontend/src/routes/import/`. Small gap: the last scene came back with 0 options (a dead end unless free speech covers it). |
| 2 | Chain includes at least one time-stop scene and one streaming scene | **Done** | The same import returned both `beginner` (time-stop) and `advanced` (live) scenes. `frontend/src/lib/components/game/GameView.svelte:178-179` (`isTimeStopped = mode !== 'advanced'`, `isLiveScenario = mode === 'advanced'`). Built-in `backend/scenarios.json` has 43 scenes: ids 1-3 beginner, 4-8 advanced. |
| 3 | Player speaks freely; system returns coherent consequences and advances | **Partly** | Time-stop turn: `GameView.svelte:374` POSTs audio to `/narrative/interaction` → `backend/services/interaction.py:42` (`process_interaction`): it transcribes (`:89`), matches options by similarity or keywords (`:168-188`), and falls back to an LLM (`invoke_google` `:332`, `openai_chat` `:345`). Live turn: `/stream/interaction` (`backend/routes/streaming.py:89`). Advancing works, but "coherent consequences" means jumping to the option's `next_scenario`. Generated free-form consequences exist only in the story player (`/narrative/generate-reaction`, `frontend/src/routes/play/story/[storyId]/+page.svelte:714`), not in the imported-chain GameView. Tests pass: `tests/process_interaction_test.py`, `streaming_interaction_test.py` (suite result below). |
| 4 | Score/lives consistent across REST and streaming, no unintentional reset | **Partly** | Run-level lives: `GameView.svelte:650-660` resets only when `!runLivesInitialized`, otherwise it clamps. One store applies REST and stream results (`frontend/src/lib/game/gameStateStore.js:203`). `runId` exists (`gameStateStore.js:26,250`). Streaming lives and penalties are tested (`tests/streaming_session_test.py:40-52`). Saving uses `/api/progress/{user_id}/{story_id}` (`backend/routes/progress.py:37,53`), but **`user_id` is a free path parameter with no auth**: `curl 127.0.0.1:8100/api/progress/anyone/anystory` reaches the handler (404 "no progress saved"), so anyone can read or overwrite anyone's progress. No test covers a REST turn followed by a stream turn and then a reload. |
| 5 | UI shows a confidence meter after each turn | **Partly** | The backend returns `confidence` (`interaction.py:126,178,188`), the store keeps it (`gameStateStore.js:203-205`) and GameView reads it (`GameView.svelte:74`). The meter component exists (`frontend/src/lib/components/scenario/ScenarioStatus.svelte:28-29`), but **nothing mounts it**: `grep -rn ScenarioStatus frontend/src` finds only its own file, and `matchConfidence` is never used in GameView markup. Players don't see a meter today. |
| 6 | Free/demo run cheap enough for marketing (pre-baked scenarios + mock streaming), no paid-tier AI | **Partly** | Pre-baked: `/demo` (`frontend/src/routes/demo/+page.svelte:11-12`, `storyStore.useBuiltInScenarios()`) returns 200, linked from the home page (`frontend/src/routes/+page.svelte:173-176`). Mock stream exists: `/stream/mock` (`streaming.py:21`), `backend/mock_stream.py`. **But:** (a) `curl 127.0.0.1:8100/api/meta` → `{"demo_mode":false,...}`, so the demo cost guards in `backend/config.py:112-118` (`story_import.py:75`, `import_routes.py:80`, `streaming.py:92`) are **off** on the live server. (b) The stream mode defaults to **`'real'`**, not mock (`frontend/src/lib/config.ts:98-99`; `/demo` only gets mock with `?stream=mock`). (c) Every time-stop demo turn still POSTs to `/narrative/interaction`, which calls Gemini for transcription and option matching (`interaction.py:89,332`). `DEMO_MODE` doesn't gate that route. So the demo is not free per turn today (cost in section 3). TTS is mostly pre-rendered: `backend/examples_audio/phrases` holds 2142 clips (633 MB), `backend/voice/cache.py:20`. |

Test suite (run from the worktree with the live venv, because the worktree has no `backend/venv`):
`PYTHON_BIN=/home/claude-user/projects/langHero/backend/venv/bin/python ./tests/test.sh` →
`50 passed, 3 skipped (JEV_API_TOKEN not set) in 2.88s`. With the default interpreter it errors on
`ModuleNotFoundError: uvicorn`, a worktree setup issue, not an app bug. The frontend suite wasn't run.

M-1 "Marketing Demo Mode" (`north-star-execution.md:36-43`) is therefore half done. The flags and mock endpoint
exist, but nothing is switched on, and the demo's main turn path (`/narrative/interaction`) is outside the flags.

## 2. What a stranger needs before paying

| Need | Exists? | Evidence | Effort |
|---|---|---|---|
| Public URL | **No** | `curl -sI https://lang.camofiles.app/` → `HTTP/2 302` to `camofiles.cloudflareaccess.com/cdn-cgi/access/login/...`. Behind CF Access, there's no public path. | **S** to flip (a Cloudflare Access policy change, David's action), but flipping it today opens unauthenticated, uncapped Gemini/TTS/import spend (rows below). Realistically **M**: it needs the demo cost guards and the rate limits first. |
| Sign-up / accounts | **Partly** (code, not configured) | Appwrite magic link and JWT: `backend/auth.py:17-84`, `frontend/src/lib/auth.ts:1-25` (`PUBLIC_APPWRITE_ENDPOINT`, `PUBLIC_APPWRITE_PROJECT_ID`), `/login` returns 200. But the live `backend/.env` holds only `CLOUDFLARE_TUNNEL_TOKEN, ELEVENLABS_API_KEY, GOOGLE_API_KEY, OPENAI_API_KEY` (no `APPWRITE_*`), `frontend/.env` only `VITE_API_URL`, and `REQUIRE_AUTH_FOR_IMPORT/PUBLISH/STREAM` default False (`config.py:136-138`). Progress isn't tied to accounts (`progress.py:37`). | **M** (Appwrite project + env + turn on the `REQUIRE_AUTH_*` flags + key progress by verified user). Shortcut **S**: use CF Access itself as the account system for paying users (email allowlist; the backend can read `Cf-Access-Authenticated-User-Email`). |
| Cheap free demo | **Partly** | See MVP row 6: pre-baked scenarios and the mock stream exist, but `demo_mode:false`, the stream defaults to real, and time-stop turns call Gemini. | **M** (force mock on `/demo`, deterministic option matching for built-in scenes with no LLM fallback, a separate `DEMO_MODE=true` backend for the public hostname so David's own instance keeps full features). |
| Paywall (entitlement check on import/generation) | **No** | `grep -rIil "stripe\|paywall\|checkout\|subscription\|paddle" backend frontend/src` (excluding venv) finds only unrelated hits (Svelte store "subscriptions", a comment in `backend/lib/ai_calls.py:28`). The closest gates are `REQUIRE_ADMIN_FOR_IMPORT` / `REQUIRE_AUTH_FOR_IMPORT` (`config.py:126-138`): admin key or any logged-in user, not "paid user". | **M** (an `entitled(user)` check on `/api/stories/import`, `/api/scenarios/from_video`, `/api/import/auto`, `/api/narratives/generate`, `/api/panels/generate-images`). **S** if "paid" = "on the CF Access allowlist". |
| Payments | **No** | Same grep: no provider SDK, no webhook, no `/pricing` (`curl 127.0.0.1:5200/pricing` → 404). | **S** for a hosted payment link with manual fulfilment (no code). **M** for checkout + webhook → entitlement. The provider depends on where David can take money (open; see the end). |
| Terms / privacy | **No** | No route under `frontend/src/routes/` (dirs: catalog, demo, import, learn, login, menu, observability, play, practice, profile, read, settings, share, story). `curl 127.0.0.1:5200/terms` → 404, `/privacy` → 404. Privacy matters here: voice audio is sent to Google/OpenAI, and D6 transcript retention is still undecided (`decision-board.md:90-99`). | **S** (two static pages + footer link). The text needs David's facts: legal entity, retention choice (D6), the processors (Google Gemini, OpenAI, ElevenLabs, typesafe.ai Jev, Appwrite). |

Also needed before any public URL (from `development/security-audit.md:73-105`, still true today): rate limiting
is off (`RATE_LIMIT_ENABLED` default False, `config.py:150`), there's no admin key, and the observability
endpoints (`/api/observability/*`) are open. `development/security-audit.md` rates "Missing authentication" as Critical
and "Cost amplification" as High.

## 3. Cost of one free demo session and one paid session

**Sources.** The ledger API (`curl -s localhost:8000/api/system/ai-calls`, `.data.windows["7d"].by_caller`)
lists 9 `langHero:*` callers, all with `"usd": null` (unpriced):

```
langHero:tts 937 calls · authored_line_grade 140 · gemini 37 (8853 in / 40258 out tok) · tutor_line_grade 37
practice_scoring 30 · openai_chat 8 (2404 in / 192 out) · jev_capability_probe 5 · romanize 1 · translate 1
```

So I priced the raw rows (`/home/claude-user/projects/orchestratorHero/storage/usage/provider_spend_host.jsonl`,
1196 langHero rows, 2026-11-21T07:46 → 2026-11-25T23:06) with the price table in
`orchestratorHero/backend/core/llm_budget.py:70-100`: gpt-4o $2.50/$10 per 1M tokens, gpt-4o-mini $0.15/$0.60,
gemini-2.5-flash $0.30/$2.50, `gpt-4o-mini-tts` $12 per 1M chars, Whisper $0.006/min. The arithmetic was an
inline python over the jsonl. Output:

```
langHero:tts                 calls= 937 usd=2.5447 ['gpt-4o-mini-tts']
langHero:gemini              calls=  37 usd=0.1033 ['gemini-2.5-flash']
langHero:openai_chat         calls=   8 usd=0.0079 ['gpt-4o']
langHero:romanize/translate  calls=   2 usd=0.0000 ['gpt-4o-mini']
langHero:practice_scoring    calls=  30  ┐
langHero:tutor_line_grade    calls=  37  │ jev-1.14.0: NO PRICE IN CODE
langHero:authored_line_grade calls= 140  │
langHero:jev_capability_probe calls=  5  ┘
tts chars 212059  avg/call 226.3  usd/call 0.002716
gemini avg in/out 239 / 1088 tokens  usd/call 0.00279
```

Total priced spend over those 5 days: **$2.66**, and **TTS is 96% of it**. Jev (`heroCommon/src/hero_common/jev_client.py:43-49`,
`https://api.typesafe.ai/v1/systemone`, billed through `console.typesafe.ai/settings/billing`) has no price
anywhere in the code. **Assumption: Jev cost is unknown and excluded**; 212 Jev calls are uncounted.

**Sessions.** "Session" isn't defined anywhere, so I used this rule: **langHero rows with no gap longer than 30
minutes form one session.** That gives 11 sessions:

```
2026-11-21T18:57  135.1min usd=1.5838 jev= 0 {'tts': 563}                         <- bulk pre-render
2026-11-22T03:19    0.8min usd=0.0226 jev=53 {gemini 9, openai_chat 3, practice 9, tutor 9, authored 35}
2026-11-23T02:26   57.6min usd=0.7013 jev=50 {tts 238, gemini 9, openai_chat 2, ...}
2026-11-24T02:26   63.3min usd=0.2931 jev=53 {tts 131, gemini 9, openai_chat 2, ...}
2026-11-25T03:19    1.0min usd=0.0344 jev=49 {gemini 9, openai_chat 1, ...}
(+6 tiny ones: 1-3 TTS clips or one translate, <$0.01 each)
```

The 1-minute sessions at 03:19-ish UTC with the identical mix (9 gemini / 35 authored / 9 tutor) look like a
scripted daily check, not a human. The two ~1-hour sessions with 131-238 TTS calls are the closest thing to real
play in the ledger.

**Free demo session (estimate).** The demo plays built-in scenes 1-8. Assume 8 turns:

| Item | Today (as shipped) | With M-1 finished (mock stream, no LLM on built-ins, cache-only TTS) |
|---|---|---|
| Turn evaluation: Gemini transcribe + match, ~1-2 calls/turn at $0.0028 | 8 × 2 × $0.0028 ≈ **$0.045** | $0 (the mock stream returns fake transcripts) |
| TTS: pre-rendered clips (2142 cached); assume ≤5 misses at $0.0027 | ≤ **$0.014** | $0 (cache only) |
| Live scenes 4-8 on `/stream/interaction` with `'real'` default: streaming transcription per partial | extra, unmeasured (no `langHero:*` stream caller in the ledger) | $0 (mock) |
| **Total** | **≈ $0.06 per demo session** (lower bound: the price table books Gemini audio input at the text rate, and real audio input costs more) | **≈ $0.00** |

So today 1,000 demo visitors cost about $60 plus abuse exposure. With M-1 finished the cost is about $0, which is
the "cheap enough for marketing" target.

**Paid session (estimate, from observed data).**

| Item | Cost |
|---|---|
| Story import, 1 Gemini call (measured today: 278 in / 3563 out tok) | $0.009 |
| ~10 turns × ~2 Gemini/OpenAI calls | ~$0.06 |
| TTS for newly generated lines (uncached): observed 131-238 clips per ~1 h session | $0.29-$0.70 |
| Jev grading: ~50 calls per session observed | **unknown (not priced in code)** |
| **Total per ~1 h paid session** | **≈ $0.35-$0.75 + Jev** |

TTS dominates, so a paid tier's margin is decided by the TTS cap. At $0.75 per session, a user who plays daily
costs about $22/month before Jev. A $10/month tier needs a cap of roughly 10-12 heavy sessions/month, or cheaper
voices, or reuse of TTS across users.

## 4. The 5 smallest steps to a first paying user (ranked)

Ranked by size and dependency. Steps 1-3 let David sell to people he can reach directly, with no public URL and
no sign-up code (paying user = an email on the CF Access allowlist). Steps 4-5 open the stranger funnel. Each one
is a queueable item.

1. **Legal pages: terms + privacy (S, code).**
   Done when: `curl -s -o /dev/null -w "%{http_code}" 127.0.0.1:5200/terms` and `/privacy` both return 200. The
   privacy page names every processor that receives user audio or text (Google Gemini, OpenAI, ElevenLabs,
   typesafe.ai Jev, and Appwrite if used) and the retention rule from D6. Both are linked from the home page
   footer. Placeholders such as `[legal entity]` are allowed only where David has to supply the fact, and each
   one is listed in the item's final message.

2. **Per-user spend guard for paid invitees (S-M, code + env).**
   Done when: with `RATE_LIMIT_ENABLED=true`, the backend reads `Cf-Access-Authenticated-User-Email` (the header
   Cloudflare sets for allowlisted users) and enforces a daily cap per email on `/api/stories/import` and on
   uncached TTS clips (defaults 5 imports and 300 clips a day, set from env). Above the cap it returns HTTP 429
   with `{"detail":"daily_limit"}`. A pytest covers under-cap, over-cap and next-day reset, and `./tests/test.sh`
   passes. Unblocks: inviting paying users without uncapped TTS risk (TTS is 96% of spend).

3. **"Get full access" call to action + manual fulfilment runbook (S, code; David picks provider and price).**
   Done when: the home page (`frontend/src/routes/+page.svelte`) shows a "Get full access" button linking to a
   URL read from `PUBLIC_PAYMENT_LINK` (hidden when unset). `development/payments-runbook.md` documents the
   manual fulfilment: payment received → add the buyer's email to the lang.camofiles.app CF Access policy →
   reply with a welcome note. The price shown matches D4 tier knobs that David has written into
   `decision-board.md`. No payment provider SDK in this step. After this, a first payer is possible.

4. **Make the demo actually ~$0 (M, code), finishing M-1.**
   Done when: `/demo` uses `/stream/mock` unless `?stream=real` is passed explicitly (`config.ts:98`). Built-in
   scenarios (ids 1-8) match options locally with no Gemini/OpenAI fallback when `DEMO_MODE=true`
   (`interaction.py:332,345`). With a backend started with `DEMO_MODE=true`, a scripted playthrough of scenes
   1-8 adds **0** `langHero:gemini`, `langHero:openai_chat` and `langHero:tts` rows to
   `provider_spend_host.jsonl`. `tests/demo_mode_test.py` asserts this, and the suite passes.

5. **Public demo hostname (M; code + David's Cloudflare action).**
   Done when: a second backend instance with `DEMO_MODE=true` and `RATE_LIMIT_ENABLED=true` runs under its own
   systemd unit, with a frontend build pointing at it. A public hostname (e.g. `demo.lang.camofiles.app`)
   answers `curl -sI` with 200 and no Access redirect, while `lang.camofiles.app` still returns 302 to Access.
   From the public host, `POST /api/stories/import` returns 401/403, `/stream/interaction` closes, and
   `/api/progress/*` and `/api/observability/*` aren't reachable. The demo page shows the step-3 call to action.
   The Cloudflare tunnel and Access change is written as one copy-paste step for David.

Deliberately not in the top 5 (bigger, not needed for payer #1): Appwrite sign-up (M), a payment webhook that
grants entitlement automatically (M), mounting the confidence meter (`ScenarioStatus.svelte`, S, but MVP polish
rather than a payment blocker), and fixing the unauthenticated `/api/progress/{user_id}` (needed with step 5's
public host, which covers it by not exposing it).

## Decisions only David can make (they block steps 3 and 5, not this doc)

- **Payment provider:** where can David legally take money (personal, CrankWheel or another entity; Stripe
  availability depends on the entity's country)?
- **Price and tier knobs (D4):** imports/day and TTS clips/day per tier, plus the monthly price. The TTS cost in
  section 3 sets the floor.
- **D6 retention** (feeds the privacy page): don't persist transcripts/audio, or aggregates only?
- **Jev pricing:** the typesafe.ai price per call, so the ledger and section 3 can include it.
