# LangHero pricing and payments: proposal for one-pass approval (2026-11-26)

David, 2026-11-26: *"we are going to need an extra source of income soon"*.

This is a proposal only. Nothing was signed up for, bought or published, and no code changed. All web figures
were read live on **2026-11-26 between 03:10 and 03:16 UTC**, from the headless browser or by fetching the page
directly. A cell reads "not shown" when the vendor's own page did not show the figure. Store prices are from the
**US** App Store in USD, and every vendor says they vary by region.

Answer sheet (section 5): **1A 2A 3B 4A 5A 6A 7A 8A**.

---

## 1. Market: what speaking-practice apps charge

| App | Price (read live) | What paid unlocks | Free / trial | Mandarin | Source |
|---|---|---|---|---|---|
| **Speak** | App Store IAP: Premium **$17.99 or $21.99/mo**, **$83.99 or $109.99/yr**. Premium Plus **$29.99 or $39.99/mo**, **$119.99 or $164.99/yr** (two price sets listed, likely regional or promotional). speak.com: "Pricing varies by plan, region, and any current promotions… within the app." | Premium: curriculum, situational roleplay, Ask Speak Tutor, smart review, custom lessons "Up to 3/day". Plus: unlimited custom lessons, unlimited Speak Tutor personalized lessons, study plan, "Target your frequent mistakes". | 7-day free trial | Yes: "Simplified Chinese (Mandarin)" | https://www.speak.com/ · https://help.speak.com/en/articles/5358417-subscription-plan-differences · https://apps.apple.com/us/app/speak-language-learning/id1286609883 |
| **Praktika** | App Store IAP: **$9.99/1 month**, **$49.99/3 months**, **$59.99 to $139.99/1 year** (several variants), promos $6.99 / $19.99. Site: "~$8/ month". | Tiers not described on its own pages (Premium = AI tutor conversations) | A "+ Trial" SKU exists; terms not shown | "Chinese" (variety not stated) | https://praktika.ai/ · https://apps.apple.com/us/app/-/id1624701477 |
| **Langua** (LanguaTalk) | **Unlimited $29.99/mo**, or $16.67/mo billed annually. **Standard $19.99/mo**, or $12.50/mo billed annually. Schools from $500/mo. | Unlimited: unlimited conversation. Standard: calls "limited to 30 minutes/day, or 75 messages" in chat. | 5-day trial (monthly) or 7-day (annual), **card required**. 30-day money-back on web/Android. | Yes, Mandarin Chinese listed | https://languatalk.com/try-langua#pricing · https://support.languatalk.com/article/142-how-much-does-langua-cost-pricing |
| **Talkpal** | App Store IAP: **$19.99/1 month**, **$49.99/3 months**, **$119.99/12 months**. talkpal.ai shows no figures ("Prices & currencies may vary depending on your location"). | Free Basic: chat with a "10 minute daily limit". Premium: "Unlimited practice with all AI modes", AI daily feedback. | Free tier, plus "14 Day Free Trial… No payment today" | Simplified + Traditional Chinese, and Cantonese | https://talkpal.ai/pricing/ · https://apps.apple.com/us/app/talkpal-ai/id6468219825 |
| **Pingo AI** | App Store IAP "Pingo Pro": **$14.99 or $17.99** (likely monthly), **$83.99 or $99.99** (likely annual). Periods not labelled. | "all conversations require a subscription" | Trial limits mentioned, terms not shown | "Chinese" (variety not stated) | https://apps.apple.com/us/app/language-learning-pingo-ai/id6738882620 |
| **Duolingo Max** | **Max price not shown** on any Duolingo page I could read (duolingo.com/max redirects to the homepage; the US App Store lists only Super Duolingo: **$9.99 / $12.99** and **$83.99 / $95.99 / $119.99**, periods not labelled). | Max = everything in Super, plus **Video Call** and **Roleplay** (blog, 2023-03-14). Super: unlimited energy, no ads, 14-day trial. | 14-day Super trial | Chinese learners get **Video Call only, no Roleplay** (blog) | https://blog.duolingo.com/duolingo-max/ · https://apps.apple.com/us/app/duolingo-language-lessons/id570060128 · https://www.duolingo.com/super |
| Loora (tried) | No price on its own site ("cost less per month than a single hour with a traditional human tutor"). English only, so not comparable. | n/a | "free trial" | No | https://loora.com/ |

**What the market tells us**
- AI speaking practice sells at **$10 to $30/mo**, with annual plans **~$60 to $165/yr**. Praktika sits at the bottom
  ($9.99/mo). Speak Premium Plus and Langua Unlimited sit at the top ($29.99 to $39.99/mo).
- Tiers are always gated by **usage** (minutes/day, messages/day, custom lessons/day), never by content.
  Langua's "30 min/day or 75 messages" and Speak's "custom lessons up to 3/day" are the same kind of knob as
  D4's imports/day and streaming min/day.
- None of them sells what LangHero has: **turn your own story, article or video into a playable, voiced,
  illustrated scenario**. Speak's "custom lessons" come closest, and Speak puts the unlimited version in its
  most expensive tier. That is a reason to put import/generation behind the paywall, which D4 already decided.
- Card-required trials (Langua) cut abuse. No-card trials (Talkpal, Speak's web start) maximise top of funnel.

## 2. What a session costs LangHero (margin input)

The launch-readiness note (task 7a14846c) does not exist yet. Costs therefore come from the **ai-calls ledger**
`orchestratorHero/storage/usage/provider_spend_host.jsonl`, rows with `caller` starting `langHero:`. There are
1,196 rows from 2026-11-21 07:46 to 2026-11-25 23:06 UTC, so this is dev traffic only. `cost_usd` is null on
every langHero row, so I priced the logged units with `orchestratorHero/backend/core/llm_budget.py`:
gpt-4o-mini-tts $12/1M chars, gpt-4o $2.50/$10, gemini-2.5-flash $0.30/$2.50 per 1M tokens, whisper $0.006/min.

| Component (caller) | Calls | Units | Cost |
|---|---|---|---|
| `tts` (gpt-4o-mini-tts) | 937 | 212,059 chars (mean 226, max 798/call) | **$2.545** |
| `gemini` (gemini-2.5-flash) | 37 | 8,853 in / 40,258 out tokens | $0.103 |
| `openai_chat` (gpt-4o) | 8 | 2,404 in / 192 out | $0.008 |
| `translate`, `romanize` (gpt-4o-mini) | 2 | ~70 tokens | ~$0 |
| `authored_line_grade`, `tutor_line_grade`, `practice_scoring`, `jev_capability_probe` (Jev) | 212 | no tokens, runs locally | ~$0 |
| **Total, 5 days** | 1,196 | | **$2.66** (by day: 1.59 / 0.02 / 0.71 / 0.29 / 0.05) |

No `gemini_image` or ElevenLabs rows fall in this window. Image cost below is an **estimate from list price**:
`gemini-2.5-flash-image` (the default, `backend/image/google.py:33`) costs **$0.039/image**, and
`gemini-3-pro-image` costs **$0.134 per 1K/2K image** (https://aistudio.google.com/docs/pricing, read
2026-11-26). The same page says gemini-2.5-flash is deprecated and routes to Gemini 3.5 Flash-Lite from
2026-12-01. That should lower the text cost, but I haven't modelled it.

**Unit costs (estimates built from the ledger figures above)**

| Unit | Assumptions | Cost |
|---|---|---|
| **Free practice session** (replay a bundled or published story, ~30 lines) | TTS served from the phrase cache (D3/D4 reuse). Grading by Jev (local). | **≈ $0.00 cached**. **≤ $0.08 worst case** if every line is uncached (30 × 230 chars × $12/1M). |
| Live streaming minute (worst case) | priced at whisper rate | $0.006/min |
| **Paid generation**: one story import or generate | LLM compile ≈ 10 gemini calls × ~1.1k out tokens ≈ $0.03. TTS for all lines ≈ 15k chars ≈ $0.18. **6 panels** on Flash image ≈ $0.23. Video import ≤ 10 min whisper ≈ $0.06. | **≈ $0.50** (≈ $1.07 if panels use Pro image) |

> **Correction (2026-11-26, master chat 5180daee).** Two inputs above are wrong; the launch-readiness note
> (`launch_readiness_20261126.md`) has them right. (1) Jev grading does not run locally: `backend/lib/jev_client.py`
> → `heroCommon/src/hero_common/jev_client.py:43` calls `https://api.typesafe.ai/v1/systemone`, billed by typesafe.ai,
> ~50 calls per session, price unknown. The margins in §3 exclude it, so they are an upper bound. (2) Appwrite is coded
> but not configured: the live `backend/.env` has no `APPWRITE_*` keys, so D1 accounts need setting up before quotas work.

## 3. Proposed tiers (fits decision-board D1, D2, D4, D5)

- **D4:** the free tier is the marketing loop, built on heavy reuse/caching. Paid unlocks story import and
  generation.
- **D1:** magic-link, email-only accounts (Appwrite is live per `project-status.md`). Every tier past anonymous
  play needs an email, which is what makes quotas enforceable.
- **D2/D5:** private by default. Publishing is explicit, and published stories feed the free tier's library.

| Knob (D4) | **Free** | **Trial** (once per account) | **Plus** |
|---|---|---|---|
| Price | $0 | $0, **no card** | **$12/mo** or **$96/yr** ($8/mo) |
| Play bundled + published stories, cached audio, Jev grading | unlimited | unlimited | unlimited |
| Story import/generation | 0 | **1 story** (≤ 5 min video) | **8 stories/mo**, max 2/day |
| Video import minutes per story | — | 5 | 20 |
| Live streaming tutor min/day | 5 | 15 (7 days) | 20 (see margin) |
| Panels per generated story | — | 6 (Flash) | 6 (Flash) |
| Saves / history | cloud saves (D1) | cloud saves | cloud saves + private library of own stories |
| Publish own story (D5 share route) | — | yes (with rights attestation, D2) | yes |

**Margin check.** Paddle is the merchant of record at 5% + $0.50 (section 4). Hosting isn't counted: it runs on
the shared VPS that David already pays for.

Gross margin = (price − Paddle fee − AI cost) / price, per month.

| Plan | Net after Paddle fee | AI cost, typical (3 stories + 10 streaming min/day) | AI cost, worst case at **20 min/day** cap (8 stories + 600 min) | AI cost, worst case if the cap were 60 min/day | Margin typical / worst (20) / worst (60) |
|---|---|---|---|---|---|
| Plus monthly $12 | $12 − $1.10 = **$10.90** | 3 × $0.50 + 300 × $0.006 = **$3.30** | $4.00 + $3.60 = **$7.60** | $4.00 + $10.80 = $14.80 | **63% / 28% / −33%** |
| Plus annual $96 ($8/mo) | $96 − $5.30 = $90.70 → **$7.56/mo** | $3.30 | $7.60 | $14.80 | **53% / ≈0% / −90%** |
| Free user, per month | — | 150 min × $0.006 ≈ **$0.90** worst case (5 min/day). Replays ≈ $0. | | | marketing cost |
| Trial, once | — | 1 × $0.50 + 7 × 15 min × $0.006 ≈ **$1.13** per signup | | | acquisition cost |

Streaming is what breaks the worst case, not generation (8 stories ≈ $4). That is why the Plus cap is **20 min/day,
not 60** (decision 3). Langua caps its Standard plan at 30 min/day for $19.99, so 20 min/day at $12 is in line with
the market. An annual subscriber who maxes out every cap breaks even, and a typical one earns 53%. The streaming
cost is priced at the whisper rate as a worst case. If live grading runs on Jev locally, as the ledger's grading
rows do, real margins are higher. The ledger is 5 days of dev traffic; once real users arrive,
re-run this margin from the ledger (the launch-readiness note should own that). The $12 price undercuts Speak,
Talkpal and Langua and sits just above Praktika, while selling a feature none of them have.

## 4. Payment route (seller: David's Icelandic company; David lives in Colombia)

| | **Stripe** (direct or Managed Payments) | **Paddle** | **Lemon Squeezy** |
|---|---|---|---|
| Accepts an **Icelandic** seller? | **No.** Iceland isn't on https://stripe.com/global (Norway and Liechtenstein are), and it isn't among the Managed Payments "Supported business locations" (https://docs.stripe.com/payments/managed-payments/eligibility). Colombia isn't on either list. | **Yes.** Paddle works with software businesses "anywhere in the world" except a sanctions list, and neither Iceland nor Colombia is on it (https://www.paddle.com/help/legal/sanctions/which-countries-are-supported-by-paddle). | **Closed.** "no longer accepting new sign-ups and will shut down on March 31, 2027" (https://www.lemonsqueezy.com/pricing, https://www.lemonsqueezy.com/) |
| Merchant of record (handles VAT/sales tax) | Only Managed Payments ("Stripe is the merchant of record"). Plain Stripe is not. | Yes: "Paddle as your Merchant of Record", tax calculation, filing and returns (https://www.paddle.com/pricing) | Yes (FAQ: "Yep."), but closing |
| Fees | Managed Payments "adds 3.5% per successful transaction to your standard Stripe processing fees" (https://stripe.com/managed-payments) | **5% + 50¢** per transaction, no monthly fee. Payouts monthly (created on the 1st, sent by the 15th), **$100/€100 minimum**. SWIFT fee $15/€15 if the payout currency doesn't match the bank's country. Up to 1.5% FX margin if converting (Paddle help: when-and-how-do-i-get-paid, is-there-a-fee-taken-for-payouts) | 5% + 50¢, "small additional fees" outside the US |
| What it needs from David | n/a for the Icelandic company. Only possible through a company in a supported country, which would be a new entity: out of scope. | 3 phases: **domain review** (live HTTPS site, product description, **pricing page**, **Terms, Refund Policy, Privacy Policy reachable from the nav**, company legal name in the Terms), **business verification** (company documents), **identity verification** (David's ID) (https://www.paddle.com/help/start/account-verification/what-is-account-verification and Paddle's domain-review guidance, read via search). Bank account for payouts: an Icelandic EUR or ISK account. Pick EUR so there's no SWIFT fee or FX if the bank is in the eurozone; otherwise expect $15/€15 per payout. | n/a |

**Recommendation: Paddle.** It is the only one of the three that will take an Icelandic company today, and it is a
merchant of record, so EU VAT and US sales tax are Paddle's problem, not David's. The 5% + 50¢ fee is the price of
not registering for VAT around the world. On a $12 plan it comes to $1.10 (9%); on the annual plan, $5.30 (5.5%).
Payouts are monthly and cover the Icelandic company. Where David's personal income ends up taxed (Colombian
residency) is a question for his accountant, not for this doc.

Two blockers to clear before applying to Paddle:
1. **Paddle's reviewer must be able to load the site.** `lang.camofiles.app` sits behind Cloudflare Access,
   so a reviewer would hit a login wall. The landing page, pricing page and legal pages need a public route
   (a public path or subdomain, with the app itself still gated).
2. **Paddle's refund rules.** The refund window must be 14 to 90 days, with no "all sales final" wording. Linking
   Paddle's own refund policy is allowed.

**Minimum legal pages** (all public and linked from the footer):
1. **Terms of Service.** Must carry the Icelandic company's **exact legal name** (Paddle rejects mismatches). Also:
   acceptable use, user content licence, the D2 rights attestation for imports, and a note that Paddle is the reseller.
2. **Privacy Policy (GDPR, because the company is in the EEA).** The data collected (email via Appwrite magic
   link, saves, voice for grading) and the processors: OpenAI, Google Gemini, Appwrite, Paddle, Cloudflare,
   ElevenLabs. The D6 transcript retention answer. Deletion rights.
3. **Refund / cancellation policy.** A 14-day window (or a link to Paddle's), and cancel anytime.
4. **Company details / imprint.** Legal name, registration number (kennitala), address, contact email.
5. **Content report / takedown contact.** An email address and a "report" link, as D2 asks.
6. **Pricing page.** Paddle's domain review requires it.

## 5. Decisions for David (answer like "1A 2A 3B …")

1. **Payment provider.** A) **Paddle** as merchant of record, applying as the Icelandic company. B) Stripe through
   a new company in a supported country. C) Wait for Lemon Squeezy (not possible: closed to new sign-ups).
   **Recommended: A.**
2. **Plus price.** A) **$12/mo or $96/yr**. B) $9.99/mo or $79/yr (Praktika level; thinner margin after the
   fixed 50¢). C) $19.99/mo or $119/yr (Langua/Talkpal level). **Recommended: A.**
3. **Plus live-streaming cap.** A) 60 min/day (worst case loses money: −33% monthly). B) **20 min/day** (worst
   case +28% monthly, ≈0% annual). C) 30 min/day (worst case +13% monthly, negative annual).
   **Recommended: B.**
4. **Plus generation quota.** A) **8 stories/mo, max 2/day, 6 Flash panels each**. B) 15 stories/mo. C)
   Unlimited stories with no panels. **Recommended: A.**
5. **Trial shape.** A) **1 free story plus 15 streaming min/day for 7 days, no card**. B) 7-day full Plus trial,
   card required (as Langua does). C) No trial. **Recommended: A.** It costs about $1.13 per signup and keeps the
   free loop open.
6. **Free tier.** A) **Unlimited play of bundled and published stories, cached audio, 5 streaming min/day, no
   imports** (D4 as written). B) The same plus 1 import/month. **Recommended: A.**
7. **Public surface for review.** A) **Put the landing, pricing and legal pages on a public route outside CF
   Access, with the app still gated.** B) Give Paddle reviewers a CF Access login. **Recommended: A.** Paddle
   checks pages that are reachable from the site's navigation.
8. **Legal pages.** A) **Draft the 6 pages above (Terms, Privacy, Refund, Imprint, Takedown, Pricing) as a follow-up
   task, with David filling in the company legal name, kennitala and address.** B) Buy a generated policy pack.
   **Recommended: A.**

Next step once answered: a follow-up task to draft the legal pages and the public pricing page. After that, David
applies to Paddle himself. Nothing is signed up for until he does.
