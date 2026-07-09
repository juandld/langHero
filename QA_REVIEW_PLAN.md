# LangHero QA Review Plan — Journey West Story

**Date:** 2026-05-25
**Route:** `/play/story/journey_west`
**Viewport sizes to test:** Desktop (1920x1080), Tablet (768x1024), Mobile (375x812)

---

## 1. Panel Images & Layout

| # | Check | Pass? |
| --- | --- | --- |
| 1.1 | Every panel image shows the character's head/face without clipping at desktop 1920x1080 | |
| 1.2 | Every panel image shows the character's head/face without clipping at tablet 768x1024 | |
| 1.3 | Every panel image shows the character's head/face without clipping at mobile 375x812 | |
| 1.4 | Images fill the entire viewport with no white/black bars on any size | |
| 1.5 | Panel transitions fade smoothly (no flash of blank/previous image) | |
| 1.6 | Gradient-only panels (no image) display a mood-appropriate gradient, not a blank screen | |
| 1.7 | All 12 prologue/ch1 panels have distinct images (no duplicate images on consecutive story panels) | |

## 2. Typewriter Text Animation

| # | Check | Pass? |
| --- | --- | --- |
| 2.1 | Narration text types out character by character with a blinking cursor (▌) | |
| 2.2 | Text does NOT repeat/restart itself once it has finished typing | |
| 2.3 | Text does NOT repeat/restart while still typing (mid-animation) | |
| 2.4 | Clicking the text box skips the animation and shows the full text immediately | |
| 2.5 | Navigating to the next panel resets the text and starts a fresh typewriter for the new panel | |
| 2.6 | Navigating back to a previous panel starts the typewriter cleanly (no leftover text from the other panel) | |
| 2.7 | Dialogue text (with speaker tag) types out after narration finishes | |
| 2.8 | Speaker tags (e.g. "◈ Bimbo", "🐵 Sun Wukong") show the correct name and icon | |

## 3. Audio & Narration

| # | Check | Pass? |
| --- | --- | --- |
| 3.1 | Clicking the 🔊 icon on narration text plays the TTS audio | |
| 3.2 | Clicking a speaker tag (e.g. "◈ Bimbo 🔊") plays the dialogue audio | |
| 3.3 | Auto-narrate toggle works: ON plays audio automatically on each new panel | |
| 3.4 | Auto-narrate toggle works: OFF does not auto-play audio | |
| 3.5 | Auto-narrate preference persists after page reload | |
| 3.6 | Volume slider adjusts playback volume in real time | |
| 3.7 | Playback speed slider (0.5x–2.0x) changes narration speed | |
| 3.8 | Sound wave animation appears during audio playback | |
| 3.9 | Stop button halts playback mid-sentence | |

## 4. Panel Navigation

| # | Check | Pass? |
| --- | --- | --- |
| 4.1 | "Next →" button advances to the next panel | |
| 4.2 | "← Back" button returns to the previous panel | |
| 4.3 | "← Back" is disabled on panel 1 | |
| 4.4 | Panel counter (e.g. "5 / 12") updates correctly | |
| 4.5 | Progress bar at top fills proportionally | |
| 4.6 | Right arrow key and Space advance panels | |
| 4.7 | Left arrow key goes back | |
| 4.8 | Clicking right half of screen advances, left half goes back | |
| 4.9 | Navigation is disabled during time freeze (except speaking) | |

## 5. Time Freeze & Speaking Mechanic

| # | Check | Pass? |
| --- | --- | --- |
| 5.1 | Time freezes automatically when reaching a panel with branching options | |
| 5.2 | "⏸ TIME FROZEN" badge appears with pulsing glow | |
| 5.3 | Particle effects and vignette overlay are visible | |
| 5.4 | Choice options display with target language text + pronunciation + translation | |
| 5.5 | Clicking a choice option plays a preview of the pronunciation | |
| 5.6 | "Speak" button appears and is tappable | |
| 5.7 | Microphone recording starts on Speak tap (browser mic permission required) | |
| 5.8 | Waveform visualization animates during recording | |
| 5.9 | Recording stops and submits for evaluation | |
| 5.10 | Result card shows tier (Perfect/Good/Passable/Fumble/Fail) with correct color | |
| 5.11 | "You said:" transcript shows what was heard | |
| 5.12 | Time resumes and game continues after result | |

## 6. Ask Bimbo (Hint System)

| # | Check | Pass? |
| --- | --- | --- |
| 6.1 | "Tell Bimbo what you want to say..." input field is visible during time freeze | |
| 6.2 | Typing a phrase and pressing Ask returns a translation hint | |
| 6.3 | The matched option highlights when Bimbo identifies a match | |
| 6.4 | Loading spinner shows while Bimbo is thinking | |
| 6.5 | Clicking the translation card plays the pronunciation audio | |

## 7. Lives, Score & Game Over

| # | Check | Pass? |
| --- | --- | --- |
| 7.1 | Hearts display correctly (full ❤️ vs empty 🖤) | |
| 7.2 | Perfect speech match grants +1 life (capped at 5) | |
| 7.3 | Failed speech reduces lives | |
| 7.4 | Chapter completion grants +1 life with animation | |
| 7.5 | Score increments based on speech match percentage | |
| 7.6 | Game over screen triggers when lives hit 0 | |
| 7.7 | "Rewind to Beginning" button resets the game fully | |

## 8. Chapter Transitions

| # | Check | Pass? |
| --- | --- | --- |
| 8.1 | Chapter transition screen shows "CHAPTER N" + chapter title | |
| 8.2 | Mood-appropriate gradient background on transition screen | |
| 8.3 | "Continue" button advances past the transition | |
| 8.4 | Auto-advance after ~4 seconds if no tap | |
| 8.5 | Life gain animation triggers on chapter complete | |

## 9. Game Menu

| # | Check | Pass? |
| --- | --- | --- |
| 9.1 | Hamburger button (☰) opens the menu | |
| 9.2 | ESC key toggles the menu | |
| 9.3 | "Exit to Menu" returns to the home screen | |
| 9.4 | Language override selector is present | |
| 9.5 | Menu closes cleanly and game resumes | |

## 10. Progress Persistence

| # | Check | Pass? |
| --- | --- | --- |
| 10.1 | Refreshing the page resumes at the last panel | |
| 10.2 | Lives, score, and reputation are restored on reload | |
| 10.3 | Branch history is preserved (choices already made stay made) | |
| 10.4 | Starting a new story begins fresh (panel 1, 3 lives, 0 score) | |

## 11. Responsive Layout

| # | Check | Pass? |
| --- | --- | --- |
| 11.1 | HUD (menu, volume, score, lives) is usable at all 3 viewport sizes | |
| 11.2 | Text box is readable and doesn't overflow at mobile width | |
| 11.3 | Nav bar (Back / counter / Next) is visible and tappable at mobile width | |
| 11.4 | Time freeze options grid reflows to single column on mobile | |
| 11.5 | Speak button is large enough to tap on mobile | |
| 11.6 | Volume control panel doesn't overflow the screen on mobile | |
| 11.7 | Chapter transition text is readable at all sizes | |

---

## Known Issues (as of 2026-05-25)

- Panels 9–12 in ch1 may share the same background image (data issue, not layout)
- Panel 8 on narrow mobile: the right-side character (purple Bimbo) can be partially cropped due to cover scaling on a wide source image

## Notes for Testers

- Test with **auto-narrate ON** for the first pass, then **OFF** for the second
- All TTS requires a working internet connection (API calls to backend)
- Microphone permission is required for speaking tests — test the deny/allow flow
- The "Dev tools" wrench icon in the top-right is for development only; verify it doesn't appear in production builds
