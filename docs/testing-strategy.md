# Testing strategy — speech, pronunciation, and the gameplay loop

Started 2026-10-20 after the autoloop stretch kept missing user-facing bugs
(invisible Speak button, forehead-cropped panels, nothing-happens-on-record).
The underlying failure mode was that every test asserted *presence* of things
(endpoint responds, DOM has test-id, grades landed in SQLite) and never *drove
the actual mic → ws → score path a learner takes*.

This doc captures (a) the research into what the field does for speech
evaluation, (b) the concrete testing targets for langHero, and (c) the
specific gameplay-loop E2E that lives in `frontend/tests/speak-loop.spec.ts`.

## What the field actually does — summary of 2026-10-20 research

### Accented-speech corpora
- **Speech Accent Archive** — 2,140 speakers from 177 countries reading the
  same passage. Good for comparing accents on identical text; small.
- **YODAS** — 369k hours of YouTube speech, unlabeled for accent/origin.
  Shape David proposed to replicate.
- **CSLU Foreign Accented English (LDC2007S08)** — licensed; includes
  Mandarin + Japanese L1 speakers of English, with accent ratings.
- **AISHELL-1 / DiDiSpeech / MELI** — large Mandarin corpora. AISHELL-1
  speakers span different accent regions of China.
- **Easy Languages (YouTube network)** — subtitled street interviews in 40+
  languages with local speakers. Closest in spirit to David's idea of
  YouTube-creator-as-benchmark. **Has not been released as a research dataset.**

### TTS quality assessment (output of ElevenLabs/OpenAI)
- **VoiceMOS Challenge 2026** — three tracks: speech enhancement MOS,
  emotional TTS MOS, accented TTS codec similarity. Organizers say
  "evaluation remains unsolved."
- **Automatic predictors (SSL-MOS, UTMOS, UTMOSv2, NISQA, DNSMOS)** — a
  June 2026 preprint found all of them track acoustic degradation well but
  are **insensitive to prosodic errors despite large subjective score drops**.
  Direct quote-level finding. Implication: automatic MOS catches bad audio
  but misses bad delivery.
- **CMOS (Comparison MOS)** — the current workaround. Play two systems on
  the same sentence, ask which is better. Avoids the MOS saturation problem
  where all modern systems cluster near the top of the scale.
- **Practical rubric** — audio_quality + custom per-dimension rubrics for
  prosody, pronunciation, naturalness, brand fit. Catches cases like a brand
  name being mispronounced where the transcript is correct.

### Pronunciation scoring (passing grades for user mic input)
- **GOP (Goodness of Pronunciation)** — Witt & Young 1998 CALL paper. Per-
  phone likelihood from an acoustic model vs. canonical. Classic reference.
- **Parikh et al. Interspeech 2025** — compared logit-based GOP variants vs.
  traditional softmax-posterior GOP on two L2 English datasets (Dutch and
  Mandarin speakers). **Max-logit GOP correlates best with human judgments.**
  Results on MPC: GOP-Margin accuracy 0.851; on SpeechOcean762 for PCC/MSE.
- **SpeechOcean762** — publicly-shared Mandarin L2 English corpus with
  expert phoneme accuracy ratings. The go-to benchmark for anyone claiming
  pronunciation scoring works.

### Novelty of David's YouTube-creator idea
No existing public dataset is built from language-learning YouTube creators
with declared L1/location. Easy Languages is the closest; it has never been
released as research data. Doing this would be genuinely new. US fair-use
law supports evaluation-only use of small clips if aggregates (not clips)
are published; CC-licensed clips are safest.

## Concrete testing targets for langHero

### 1. End-to-end gameplay loop — the one shipped alongside this doc
Simulate a learner reaching a time-freeze panel and speaking a response.
Full stack driven: Playwright → fake microphone (Chrome --use-file-for-fake-
audio-capture flag) → MediaRecorder → WebSocket to `/stream/interaction` →
backend transcription + scoring → `event: final` → frontend `onFinal`
callback → result card renders.

Lives at `frontend/tests/speak-loop.spec.ts`. Fixture WAV at
`frontend/tests/fixtures/learner-sample.wav` (converted from one of our
ElevenLabs mp3 outputs so the voice reads as fluent Japanese).

Pass criteria: `event: final` arrives within 10 seconds, result card
`[data-testid="speak-result"]` becomes visible in the DOM.

Catches: any regression in the full mic→WS→backend→UI chain. Including:
- getUserMedia / MediaRecorder changes
- Websocket URL misconfiguration
- Backend scenario-mode scoring breaking (as happened in #2135/#2136)
- Frontend `onFinal` callback never firing (as the `penalty-instead-of-final`
  bug would produce)

### 2. YouTube creator benchmark (not yet built, prioritized)
`tests/corpora/youtube_accents.json` with ~50 entries. Each entry:
```json
{
  "creator": "Learn Japanese with Yuta",
  "declared_l1": "Japanese",
  "declared_region": "Tokyo",
  "clip_path": "tests/corpora/clips/yuta_01.wav",
  "whisper_transcript": "...",
  "expected_native_score_min": 0.80
}
```
Nightly cron: feed each clip through `/api/practice/chat`; assert Jev scores
`naturalness` and `register_fits` ≥ expected. If scores diverge wildly by
region (e.g., Taiwanese Mandarin consistently scored lower than Beijing),
surface as a fairness regression.

Licensing: clips stay on this VPS, aren't redistributed, only aggregate
metrics are published. CC-filtered YouTube search for safest clips. Use
`yt-dlp` with `--download-sections "*00:00-00:30"` for small samples.

### 3. SpeechOcean762 pronunciation validation (not yet built)
Validate our pronunciation scoring (whether that's a new GOP implementation
or Jev's existing scoring) correlates with human experts. Metric: Pearson
≥ 0.6 between our score and SpeechOcean762 human ratings. Below that, the
grade a learner sees is noise.

### 4. CMOS A/B when swapping TTS providers (not yet built)
When comparing ElevenLabs vs. OpenAI vs. future providers, ask Jev for
pairwise preference on the same sentence, not an absolute MOS. Matches 2026
best practice from the research. Jev already handles register/naturalness
judgments so this is a thin wrapper around existing graders.

### 5. Prosody-specific check (not yet built)
Forced alignment via Montreal Forced Aligner → per-phone duration →
compare to canonical prosody for the sentence type (question → rising).
Flags outliers. Fills the exact gap the VoiceMOS 2026 research identified
in automatic MOS models.

### 6. Fairness audit (not yet built)
Load Speech Accent Archive, pick 50 speakers reading identical content.
Score through Jev. If grades correlate with speaker L1 or region beyond
actual quality variance, document as a bias finding. Not for shipping to
users; for internal visibility.

## Priority order (recommended)

1. **E2E gameplay loop test** — shipped with this doc. Catches regression
   of the exact bugs that slipped past the autoloop stretch.
2. **YouTube creator benchmark MVP** — 20 creators, nightly grading,
   dashboard shows per-region native-speaker baseline. ~1 week.
3. **SpeechOcean762 validation** — proves pronunciation scoring correlates
   with experts; gives a public benchmark score to point at. ~3 days.
4. **CMOS TTS A/B** — ~1 day; before any provider swap.
5. **Prosody check + fairness audit** — later; good hygiene.

## Sources

- Parikh et al. 2025 — Logit-Based GOP Scores for Mispronunciation Detection
  https://arxiv.org/pdf/2506.12067
- Witt & Young 1998 — original Goodness of Pronunciation measure
  https://mi.eng.cam.ac.uk/reports/abstracts/witt_still98.html
- VoiceMOS Challenge 2026 — https://arxiv.org/pdf/2609.13792
- Easy Languages (YouTube) — https://en.wikipedia.org/wiki/Easy_Languages_(YouTube)
- YODAS — 369k-hour YouTube corpus — https://arxiv.org/pdf/2205.08014
- AISHELL-1 — https://openslr.org/33
- DiDiSpeech — https://arxiv.org/pdf/2010.09275
- MELI (Mandarin-English Language Interview) — https://arxiv.org/html/2603.27043v1
- CSLU Foreign Accented English — https://catalog.ldc.upenn.edu/LDC2007S08
- SELL-Corpus (multi-accented Chinese-English L2) —
  https://sigport.org/sites/all/modules/pubdlcnt/pubdlcnt.php?fid=5638
- Soniox — Evaluating TTS Quality (CMOS methodology) —
  https://soniox.com/wiki/evaluating-tts
- Future AGI — How to Evaluate TTS Quality in 2026 —
  https://futureagi.com/blog/how-to-evaluate-tts-quality-voice-ai-2026/
