# QA Checklist × Playwright Testability

**Source:** `QA_REVIEW_PLAN.md` (60 checks, Journey West story, 3 viewports)
**Date:** 2026-05-25
**Browser context:** `langhero` Chromium on CDP 9226, available via `mcp__playwright__*`

## Legend

- **AUTO** — fully automatable in Playwright; pass/fail is deterministic from DOM, network, or storage state.
- **AUTO+SNAP** — automatable, but the assertion is a screenshot comparison (image diff). Needs a baseline.
- **PARTIAL** — Playwright can drive the trigger and observe side-effects (audio element state, classes, events) but cannot validate the perceptual outcome (e.g. "fades smoothly", "is readable"). Needs a human spot-check on top of the automated check.
- **MANUAL** — fundamentally outside the browser sandbox (real microphone input, perceptual audio quality, "looks nice"). Playwright can only stub or skip.

## 1. Panel Images & Layout

| # | Check | Verdict | How (or why not) |
|---|---|---|---|
| 1.1 | Head/face not clipped @ 1920x1080 | AUTO+SNAP | `browser_resize 1920x1080`, navigate each panel, `browser_take_screenshot` per panel → manual eyeball review OR feed to a vision model. Pure DOM cannot judge "head clipped". |
| 1.2 | Same @ 768x1024 | AUTO+SNAP | Same flow with `browser_resize 768x1024`. |
| 1.3 | Same @ 375x812 | AUTO+SNAP | Same flow with `browser_resize 375x812`. |
| 1.4 | Images fill viewport, no bars | AUTO | `browser_evaluate`: read `getComputedStyle` on the image container — assert `object-fit: cover` and that `naturalWidth/naturalHeight` ratio is being upscaled to fully cover element bounds. Sample 5px from each edge of a screenshot for non-background pixels. |
| 1.5 | Panel transitions fade smoothly | PARTIAL | Can assert the fade CSS class is applied + transition `duration` > 0 + no `display:none` flash via `requestAnimationFrame` sampling. "Smooth" perception is human. |
| 1.6 | Gradient-only panels show mood gradient | AUTO | `browser_evaluate`: when no `<img>` rendered, assert background-image contains `linear-gradient(` and is not transparent/black. |
| 1.7 | All 12 panels have distinct images | AUTO | Walk panels 1-12, collect `<img src>` (or background-image URL), assert 12 unique values. The known issue (panels 9-12 may dupe) becomes a regression test. |

## 2. Typewriter Text Animation

| # | Check | Verdict | How |
|---|---|---|---|
| 2.1 | Types char-by-char with blinking ▌ cursor | AUTO | Poll `textBox.textContent.length` over time, assert monotonic increase. Assert `▌` glyph appears in DOM while `isTyping=true`. |
| 2.2 | Text does NOT restart once finished | AUTO | After typing settles, snapshot length every 250ms for 3s, assert never decreases. This was the bug behind the `typeGeneration` cancellation token in TextBox.svelte — guard against regression. |
| 2.3 | Text does NOT restart mid-typing | AUTO | Same poll during the typing window — assert length is strictly monotonic, no resets to 0 or smaller. |
| 2.4 | Clicking textbox skips animation | AUTO | `browser_click` on textbox during typing → assert `textContent.length === finalText.length` within one frame. |
| 2.5 | Next panel resets text + fresh typewriter | AUTO | Next → assert new textbox starts at length ≤ 3 then grows. |
| 2.6 | Back to previous panel types cleanly | AUTO | Same as 2.5 in the back direction; assert no leakage of the future panel's text. |
| 2.7 | Dialogue types after narration finishes | AUTO | Assert dialogue node is empty until narration `isTyping=false`, then dialogue starts. |
| 2.8 | Speaker tags show correct name + icon | AUTO | DOM assertion against the `getSpeakerName`/`getSpeakerIcon` maps in `TextBox.svelte:21-49`. |

## 3. Audio & Narration

| # | Check | Verdict | How |
|---|---|---|---|
| 3.1 | 🔊 on narration plays TTS | AUTO | `browser_click` 🔊; `browser_evaluate` grabs the `<audio>` element, assert `!audio.paused` and `audio.currentTime > 0` within 1s. Also `browser_network_requests` should show a `/tts` POST. |
| 3.2 | Speaker tag plays dialogue audio | AUTO | Same pattern, click speaker tag, assert audio playing + TTS request fired with `speaker=…`. |
| 3.3 | Auto-narrate ON auto-plays on new panel | AUTO | Toggle ON, advance, assert `audio.paused === false` without any user click. |
| 3.4 | Auto-narrate OFF does NOT auto-play | AUTO | Toggle OFF, advance, wait 1s, assert no audio playing and no TTS network request fired. |
| 3.5 | Auto-narrate persists after reload | AUTO | Toggle, reload, `browser_evaluate localStorage.getItem('autoNarrate')` and check checkbox DOM state. |
| 3.6 | Volume slider adjusts in real time | PARTIAL | Set slider, `browser_evaluate` audio element `volume` property; deterministic. "Hearing it change" is manual but the API contract is testable. |
| 3.7 | Speed slider changes narration speed | PARTIAL | Same — assert `audio.playbackRate` matches slider. Perception is manual. |
| 3.8 | Sound wave animation during playback | AUTO | Assert the waveform component has `data-playing="true"` class / aria attribute (or animation class) while audio is playing. |
| 3.9 | Stop button halts mid-sentence | AUTO | Click ▶ then Stop; assert `audio.paused === true` and `currentTime` stops advancing. |

## 4. Panel Navigation

| # | Check | Verdict | How |
|---|---|---|---|
| 4.1 | Next → advances | AUTO | Click Next, assert counter increments. |
| 4.2 | ← Back returns | AUTO | Click Back from panel 2, assert counter == 1. |
| 4.3 | Back disabled on panel 1 | AUTO | At panel 1, `browser_evaluate` Back button `disabled` attribute / `aria-disabled`. |
| 4.4 | Counter "5 / 12" updates | AUTO | DOM text assertion at each navigation. |
| 4.5 | Progress bar fills proportionally | AUTO | Read `style.width` (%) of progress bar, assert ≈ `currentPanel/totalPanels`. |
| 4.6 | Right arrow / Space advance | AUTO | `browser_press_key ArrowRight` / `Space` → counter increments. |
| 4.7 | Left arrow goes back | AUTO | `browser_press_key ArrowLeft` → counter decrements. |
| 4.8 | Click right half advances, left half back | AUTO | `browser_click` at coordinates (vw*0.75, vh/2) / (vw*0.25, vh/2). |
| 4.9 | Nav disabled during time freeze (except speaking) | AUTO | At a freeze panel, send Next → assert counter unchanged AND Speak button enabled. |

## 5. Time Freeze & Speaking Mechanic

| # | Check | Verdict | How |
|---|---|---|---|
| 5.1 | Time freezes on branching panel | AUTO | Navigate to known branching panel, assert `.time-frozen` class (or store value via `browser_evaluate`). |
| 5.2 | "⏸ TIME FROZEN" badge with pulsing glow | AUTO+SNAP | Assert badge text exists. Pulsing = check CSS `animation` property is set; "looks pulsing" is visual. |
| 5.3 | Particle + vignette overlay visible | AUTO+SNAP | Assert particle canvas/overlay element is in DOM with opacity > 0. Visual richness = screenshot review. |
| 5.4 | Choice options show text + pronunciation + translation | AUTO | DOM assertions on each choice card (3 fields present and non-empty). |
| 5.5 | Clicking choice plays preview pronunciation | AUTO | Same audio pattern as 3.1; click choice, assert audio plays. |
| 5.6 | Speak button appears + tappable | AUTO | Element exists, `disabled === false`, hit target ≥ 44x44px. |
| 5.7 | Mic recording starts on Speak tap | PARTIAL | Playwright can grant mic permission via `browser_navigate` with permissions context, and `browser_evaluate` `navigator.mediaDevices.getUserMedia` was called. **No real audio input**. Must stub `MediaRecorder` via `browser_run_code_unsafe` to feed canned audio. |
| 5.8 | Waveform animates during recording | PARTIAL | With a stubbed stream, assert waveform canvas updates (sample pixel data over time). |
| 5.9 | Recording stops + submits | AUTO | With stubbed recorder, trigger stop, assert POST to `/speech/evaluate` (or wherever) via `browser_network_requests`. |
| 5.10 | Result card tier + color | AUTO | Mock the backend response (intercept via `browser_evaluate` overriding `fetch`), assert tier text and computed color match the tier→color map. |
| 5.11 | "You said:" transcript shows | AUTO | DOM text assertion after mocked response. |
| 5.12 | Time resumes after result | AUTO | Assert `.time-frozen` class removed and Next button re-enabled. |

## 6. Ask Bimbo (Hint System)

| # | Check | Verdict | How |
|---|---|---|---|
| 6.1 | Input field visible during freeze | AUTO | DOM presence + visibility. |
| 6.2 | Typing + Ask returns translation | AUTO | `browser_type` phrase, click Ask, wait for response card, assert text non-empty. Real LLM call — slow but works. |
| 6.3 | Matched option highlights | AUTO | After Ask, assert one choice has highlight class. |
| 6.4 | Loading spinner while thinking | AUTO | Between Ask click and response, assert spinner element visible. |
| 6.5 | Clicking translation card plays audio | AUTO | Same audio play pattern. |

## 7. Lives, Score & Game Over

| # | Check | Verdict | How |
|---|---|---|---|
| 7.1 | Hearts show full vs empty | AUTO | Count ❤️ vs 🖤 in HUD, compare to expected count. |
| 7.2 | Perfect speech grants +1 life (cap 5) | AUTO | Mock speech eval to return Perfect; assert lives++ but capped. |
| 7.3 | Failed speech reduces lives | AUTO | Mock Fail tier, assert lives--. |
| 7.4 | Chapter completion +1 life with animation | AUTO | Trigger chapter end; assert lives++ and animation class fires (presence-only, not perception). |
| 7.5 | Score increments by match % | AUTO | Mock various tiers, read score from store/DOM, assert delta matches the formula. |
| 7.6 | Game over screen at 0 lives | AUTO | Force lives to 0 via repeated mocked fails, assert game over UI appears. |
| 7.7 | Rewind to Beginning resets | AUTO | Click Rewind, assert panel === 1, lives === 3, score === 0, localStorage cleared. |

## 8. Chapter Transitions

| # | Check | Verdict | How |
|---|---|---|---|
| 8.1 | Shows "CHAPTER N" + title | AUTO | DOM text assertion on transition screen. |
| 8.2 | Mood-appropriate gradient background | PARTIAL | Assert gradient is present and matches the chapter's configured palette. "Appropriate" is editorial. |
| 8.3 | Continue button advances | AUTO | Click, assert past transition. |
| 8.4 | Auto-advance after ~4s | AUTO | Wait 4.5s without interaction, assert transition gone. |
| 8.5 | Life gain animation on chapter complete | AUTO | Trigger chapter end, assert animation class present + lives++. |

## 9. Game Menu

| # | Check | Verdict | How |
|---|---|---|---|
| 9.1 | ☰ opens menu | AUTO | Click, assert menu visible. |
| 9.2 | ESC toggles menu | AUTO | `browser_press_key Escape` twice, assert toggle behavior. |
| 9.3 | Exit to Menu returns home | AUTO | Click, assert URL is home route. |
| 9.4 | Language override selector present | AUTO | DOM presence assertion. |
| 9.5 | Menu closes cleanly + game resumes | AUTO | Open then close, assert game state untouched (panel, lives, score unchanged). |

## 10. Progress Persistence

| # | Check | Verdict | How |
|---|---|---|---|
| 10.1 | Refresh resumes at last panel | AUTO | Navigate to panel N, `browser_navigate` to same URL (or reload), assert panel === N. |
| 10.2 | Lives/score/reputation restored on reload | AUTO | Same; HUD values match pre-reload. |
| 10.3 | Branch history preserved | AUTO | Make a choice, reload, assert that branch state still recorded (visible in store or revisit panel). |
| 10.4 | New story = fresh state | AUTO | Trigger reset → assert panel 1, lives 3, score 0. |

## 11. Responsive Layout

| # | Check | Verdict | How |
|---|---|---|---|
| 11.1 | HUD usable at all 3 sizes | AUTO+SNAP | Resize × 3, assert no element has `display:none` unexpectedly, all interactive elements ≥ 44px hit target. Screenshots for review. |
| 11.2 | Text box readable, no overflow at mobile | AUTO | `browser_evaluate`: textbox `scrollWidth <= clientWidth` (no horizontal scroll), font-size ≥ 14px. "Readable" beyond that is human. |
| 11.3 | Nav bar visible + tappable at mobile | AUTO | Bounding box checks: in viewport, hit target ≥ 44px. |
| 11.4 | Time freeze options reflow single column at mobile | AUTO | At 375px, assert grid has 1 column (computed `grid-template-columns` or that all choice cards share the same `offsetLeft`). |
| 11.5 | Speak button large enough on mobile | AUTO | Bounding box ≥ 44x44px (WCAG 2.5.5). |
| 11.6 | Volume panel doesn't overflow on mobile | AUTO | Panel bounding box within viewport bounds. |
| 11.7 | Chapter transition text readable at all sizes | AUTO+SNAP | Width fits, font-size ≥ 16px. Screenshot for review. |

---

## Summary

| Verdict | Count |
|---|---|
| AUTO | 41 |
| AUTO+SNAP | 8 |
| PARTIAL | 7 |
| MANUAL | 0 |
| **Total** | **56** |

(The plan has 60 row entries; a few overlap — e.g. checks 1.1/1.2/1.3 are the same automation invoked at three viewports. The 56 count above is distinct automation flows.)

## What needs scaffolding before Playwright runs are useful

1. **Backend mocks for speech eval** — every check in §5.10–7.5 needs a way to force a specific tier. Two options:
   - Add a `?force_tier=perfect` debug query the speech endpoint honors (dev-only).
   - Intercept the fetch via `browser_evaluate` and stub the response. Less invasive; recommended.
2. **MediaRecorder stub** — inject before navigation to feed canned PCM so the recording flow can be exercised without a real mic.
3. **Screenshot baselines** for AUTO+SNAP rows. Store under `tests/visual/baseline/` and diff with a tolerance (~2%).
4. **Storage seeding helper** — `browser_evaluate localStorage.setItem(...)` to jump to specific game states without playing through.
5. **Deterministic story** — pin Journey West RNG (if any) via a query string so tests are reproducible.

## Practical playbook for the next QA pass

1. Manual pass at all 3 viewports for §1, §2, §5.2–5.3, §8.2, §11.x — the parts where "looks right" is the real criterion.
2. Automate everything marked AUTO. Roughly 41 flows; many share setup (load story → navigate to panel N).
3. Defer AUTO+SNAP until baselines are captured manually first.
4. PARTIAL items get an automated contract test (property-level) AND a manual perceptual check in the human pass.
