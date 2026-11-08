---
name: investigate
description: Run a Jev-powered investigation tournament on any topic — fetch sources, extract the most-relevant quotes via calibrated paragraph scoring, and emit a structured research packet with typed answers to meta questions. Use whenever the user asks to research/investigate/dig-into a company, technology, person, decision, or general topic and you have one or more sources (URLs, files) to base the answer on.
metadata:
  author: claude
  version: "1.0"
---

# /investigate — Jev-powered research tournament

Turn "look into X" into a structured, cited, confidence-scored answer.

## When to invoke

- User says "investigate <thing>", "research <thing>", "what's relevant about <thing>", "dig into <topic>".
- You need a rigorous view of a company/tool/person you're about to reference in a decision, draft, or plan.
- You have one or more sources (URLs, local files) and want the SIGNAL extracted from them — the paragraphs that matter, with calibrated confidence per axis.
- Before writing outreach copy: run this on the recipient's domain to get real quotes to anchor the hook.

## When NOT to invoke

- The user's question is answerable from your own knowledge without external fetching. This isn't a general search — it needs concrete sources.
- Time-critical work where a 5-10s Jev batch is too slow.

## What it does

1. Fetch each source (URL → HTML → paragraphs; file → paragraphs; stdin → paragraphs).
2. Rank paragraphs using the chosen method (default: `hierarchical`).
3. Top-K survive → ask typed meta questions (Choice / Score / Noul) using top-K as state.
4. Emit a JSON packet with sources, top quotes with per-axis scores, and meta answers with confidences.

### The method choice — a real fight, decided empirically

A method tournament ran 5 candidates against 5 topics (3 lead pages + 2 technical docs), with Jev itself judging pairwise duels for which method's top-5 better answered each topic. Bias-corrected via both-orderings. Full Elo:

| # | Method | Elo | Avg wall | Avg API calls | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | **`hierarchical`** | **1553** | 1.0s | 40 | 3-stage funnel: cheap filter → deep multi-Noul → depth Scores. **Default.** |
| 2 | `solo` | 1520 | 0.5s | 22 | Weighted-sum Nouls in one pass. ~2× faster and cheaper. Use for batch/cost-constrained work. |
| 3 | rubric_derived | 1503 | 0.6s | 23 | Jev picked questions first, then applied. Marginal gain, extra setup call. |
| 4 | fanout | 1479 | 0.5s | 22 | 10 Nouls per paragraph; density signal. Loses to focused methods. |
| 5 | length_only | 1445 | 0.0s | 0 | No Jev — sanity baseline. Beaten by every Jev method. |

`--method hierarchical` (default) vs `--method solo` (fast/cheap fallback). Full results: `orchestratorHero/scripts/jev/jev_method_tournament_results.json`.

### Presets bundled (define WHAT to score; method defines HOW)

| preset | axes | meta questions |
| --- | --- | --- |
| `lead` | specific_business_detail, crankwheel_fit_signal, describes_process | industry (Choice), sales_shape (Choice), uses_screen_share (Noul), crankwheel_fit_score (Score) |
| `generic` | topically_relevant, specific_detail, quotable | coverage (Score), conflicting_evidence (Noul) |

Custom axes/questions: pass `--custom-questions path/to/questions.json` overriding either preset field.

## How to call

```bash
python3 /home/claude-user/projects/orchestratorHero/scripts/jev_investigate.py \
  --topic "How does Jev's API differ from OpenAI's chat completions?" \
  --source https://typesafe.ai/blog/introducing-system-one-models-and-jev \
  --source https://docs.typesafe.ai/introduction/quickstart.md \
  --preset generic \
  --method hierarchical \
  --fetcher auto \
  --top-k 5 \
  --out /tmp/jev_vs_openai.json
```

For batch or cost-constrained work, override with `--method solo` — 2× faster, ~33 Elo behind but still well above baseline.

## Fetchers — when to use the browser vs plain HTTP

| Fetcher | Speed | JS rendered | Passes CF/DD | When to use |
| --- | --- | --- | --- | --- |
| `requests` | ~0.3s | no | rarely | Default for server-rendered marketing sites; identical output to a fully-scrolled browser on those. |
| `chromium` | ~1-3s | yes | tier-1 CF only | JS-only pages (SPAs, dashboards) where the initial HTML is a stub. |
| `auto` **(default)** | dynamic | yes on fallback | tier-1 CF only | Tries `requests` first; falls back to `chromium` if the response is thin (<3 paragraphs), a challenge page, or an HTTP error. Best general choice. |

**Verified live:** `auto` on `https://prospeo.io/pricing` — requests returned 0 paragraphs (SPA stub), chromium recovered 22. Fetcher choice is recorded per-source in the packet's `sources_fetched[].fetcher_used` field.

**Beyond tier-1:** for hard filters (Cloudflare Turnstile, Datadome — verified live on `g2.com`, `trustradius.com`), even the headless chromium fetch is caught. The escalation ladder:

**Level 1 — scripted (default).** `jev_investigate.py --fetcher auto`. Handles most sites. Records `fetcher_used` per source.

**Level 2 — agent-driven fetch via the connected chromium.** When Level 1 returns 0-2 paragraphs or a challenge marker, the AGENT (Claude) escalates. Recipe:

```
1. browser_navigate the target URL in the connected chromium (David's real
   session — real cookies, real fingerprint, tier-1 CF passes silently).
2. Wait for load; optionally browser_evaluate to scroll top-to-bottom so
   lazy-loaded content fires (see the RPOA scroll pattern).
3. browser_evaluate to dump the fully-rendered HTML:
     () => document.documentElement.outerHTML
4. Save to /tmp/level2.html.
5. python3 jev_investigate.py --source /tmp/level2.html --topic "..." --preset ...
   (auto-detected as HTML because it starts with <!doctype html> or <html>.)
```

**Level 3 — human-in-the-loop.** When Level 2 hits a challenge page (Turnstile, Datadome). Recipe:

```
1. Agent fires a Telegram via jev_client's watchdog: "⚠ /investigate blocked on
   <site> — click through the challenge in your VNC chromium, then reply
   'retry <task_id>'."
2. David opens the site in his connected chromium, solves the challenge once,
   session cookies persist.
3. On David's 'retry' reply, agent re-runs Level 2 — challenge no longer fires
   because the session is now trusted.
```

**Launch config staged, restart-gated.** `llmTerminal/web/scripts/sync-config.py` has been updated to add `--remote-allow-origins=*` to the chromium systemd units. Unlocks CDP-from-scripts, which enables a future `--fetcher connected` where Python (not just the agent) can hit David's live session directly. Activate with:

```bash
sudo python3 /home/claude-user/projects/llmTerminal/web/scripts/sync-config.py
sudo systemctl daemon-reload
sudo systemctl restart chromium-orchestratorhero chromium-crankhero chromium-camohero chromium-llmterminal chromium-langhero
```

Output is JSON. Keys: `topic`, `preset`, `sources_fetched[]`, `n_paragraphs_scored`, `paragraph_scoring_seconds`, `top_quotes[]` (each with `text`, `source`, `scores`, `combined`), `meta_answers` (typed answers with `confidence` + `probabilities`).

## Typical cost / latency

- 1 URL / 20-40 paragraphs: **~USD 0.01, 1-3s wall time**
- 5 URLs / 100+ paragraphs: **~USD 0.05, 5-10s**
- Every axis added costs ~USD 2e-5 per paragraph. Add liberally.

## Interpreting the output

- **`meta_answers[X].confidence`** tells you whether to trust the answer or route to human. High confidence + strong verdict = act. Low confidence = the sources are ambiguous, fetch more.
- **`top_quotes[].scores`** — inspect per-axis breakdown to understand *why* a paragraph ranked high. Big spread = paragraph is strong on one dimension only.
- **Redirect anomalies** — if `sources_fetched[].resolved_to` domain != the source's original host, the target got redirected (possible acquisition, rebrand, or dead site). Surface this.

## Prerequisites

- `TYPESAFE_API_KEY` in env or in `crankHero/.env` (auto-read).
- Python `requests` + `lxml` (both preinstalled).
- Script lives at `orchestratorHero/scripts/jev_investigate.py` — call from any chat via that absolute path.

## Relationship to the existing dataHero investigation pipeline

`dataHero/ingestion/{company_research, investigation_run, lead_investigator}.py` is a specialized batch pipeline for scheduled campaign runs — with cost caps, QA gates, dry-run defaults, and provider abstraction (homepage / Apollo / deep-agent). That pipeline **stays**. It is the correct tool for "investigate all 1779 tier-2 CA leads with a $X budget" — not this skill.

**Use `/investigate` for:**
- Ad-hoc single-topic research inside a chat
- Interactive research before writing a hook, drafting a doc, or answering a decision
- A tight, calibrated packet returned in 1-3 seconds

**Use the dataHero pipeline for:**
- Scheduled or batched cost-capped runs across N leads
- Anything that needs the investigation-QA gate (`investigation_qa.py`)
- Persistence into `lead_verdicts` and downstream tier assignment

The two can share evidence: a Jev packet from `/investigate` is a valid provider tier for the dataHero pipeline's homepage phase. Wiring is future work.

## Extensions

- Batch across many leads via Jev: `crankHero/campaigns/jev_lead_batch.py` wraps the script with a SQL query over `crm.db` and per-row persistence to `campaigns/lead_investigations/<lead_id>.json`. Complements — does not replace — the dataHero pipeline.
- Custom presets: write a JSON with `paragraph_nouls`, `paragraph_weights`, `meta_questions` and pass with `--custom-questions`.

## Cross-project availability

Currently scoped to orchestratorHero. To make invokable in other project chats, copy this file to each sibling project's `.claude/commands/investigate.md`, OR (better) drop into `~/.claude/commands/investigate.md` for user-global (needs the user to move it — the harness blocks agent writes under `~/.claude/`).

## Don't

- Don't investigate without at least one concrete source. This isn't a general web search.
- Don't set the topic to a leading question ("Is X the best tool?") — Jev will find whatever the sources say. Write a neutral topic.
- Don't skip `--top-k` when the source is huge; the meta call gets the full top-K as state.
