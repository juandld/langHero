<script>
  import { onMount, onDestroy } from 'svelte';
  import { page } from '$app/stores';
  import { browser } from '$app/environment';
  import { fade, fly, scale } from 'svelte/transition';
  import { getApiBase, getTTS } from '$lib/api';
  import { masterVolume, playbackSpeed } from '$lib/audioStore';
  import { STORAGE_KEYS, getString, getJson, setJson } from '$lib/utils/storage';
  import { createStreamingManager } from '$lib/game/streamingManager';
  import { createRecordingSession, ensureAudioContext, playBeep, setupAudioAnalyser, disconnectAnalyser } from '$lib/game/audioUtils';
  import { createAudioEngine } from '$lib/game/audioEngine';
  import { RESPONSE_CATEGORIES, STYLE_TO_CATEGORY, getOptionCategory, getCategoryKey, resolveBranch, resolvePanel, findPanelLocation, buildCategoriesFromSkeleton, setActiveCategories } from '$lib/game/branchLogic';
  import { fetchTtsUrl } from '$lib/utils/ttsCache';
  import { createStoryLoader } from '$lib/game/storyLoader';
  import { checkBimboHint, resetBimboHints } from '$lib/game/bimboHints';
  import { t, uiLangFor } from '$lib/game/i18n';

  // Game components
  import GameHUD from '$lib/components/game/GameHUD.svelte';
  import TimeStopPanel from '$lib/components/game/TimeStopPanel.svelte';
  import SpeakButton from '$lib/components/game/SpeakButton.svelte';
  import VolumeControl from '$lib/components/game/VolumeControl.svelte';
  import GameMenu from '$lib/components/game/GameMenu.svelte';
  import { DevTools } from '$lib/devtools/index.js';
  import SpeakResultCard from '$lib/components/game/SpeakResultCard.svelte';
  import TextBox from '$lib/components/game/TextBox.svelte';
  import GameOverOverlay from '$lib/components/game/GameOverOverlay.svelte';
  import SegmentLoading from '$lib/components/game/SegmentLoading.svelte';
  import ChapterTransition from '$lib/components/game/ChapterTransition.svelte';
  import LifeGain from '$lib/components/game/LifeGain.svelte';
  import EndingScreen from '$lib/components/game/EndingScreen.svelte';

  const API_BASE = getApiBase();
  const AUTO_NARRATE_KEY = 'LANGHERO_AUTO_NARRATE_V1';

  // Narration language/level — which language the story is told/spoken in,
  // and the vocabulary complexity. Persisted across sessions; a change
  // reloads the current story so every fetch uses the new setting
  // consistently (no stale-language panels mixed into the same run).
  let narrationLanguage = loadNarrationLanguage();
  $: uiLang = uiLangFor(narrationLanguage, story);
  $: assistantName = (story && story.assistant && story.assistant.name) || 'Bimbo';
  let narrationLevel = loadNarrationLevel();

  function loadNarrationLanguage() {
    if (!browser) return '';
    try { return localStorage.getItem(STORAGE_KEYS.NARRATION_LANGUAGE) || ''; } catch (_) { return ''; }
  }

  function loadNarrationLevel() {
    if (!browser) return 'beginner';
    try { return localStorage.getItem(STORAGE_KEYS.NARRATION_LEVEL) || 'beginner'; } catch (_) { return 'beginner'; }
  }

  function storyFetchQuery() {
    if (!narrationLanguage) return '';
    return `?language=${encodeURIComponent(narrationLanguage)}&level=${encodeURIComponent(narrationLevel)}`;
  }

  function handleUpdateNarrationLanguage(e) {
    const value = e.detail || '';
    if (value === narrationLanguage) return;
    narrationLanguage = value;
    if (browser) {
      try { localStorage.setItem(STORAGE_KEYS.NARRATION_LANGUAGE, value); } catch (_) {}
    }
    // Re-fetch rather than patch in place: every loaded chapter/segment needs
    // the new language, and stale segmentCache entries must not leak through.
    window.location.reload();
  }

  function handleUpdateNarrationLevel(e) {
    const value = e.detail || 'beginner';
    if (value === narrationLevel) return;
    narrationLevel = value;
    if (browser) {
      try { localStorage.setItem(STORAGE_KEYS.NARRATION_LEVEL, value); } catch (_) {}
    }
    window.location.reload();
  }

  // Mood-based gradient backgrounds for panel images
  const MOOD_GRADIENTS = {
    contemplative: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
    warm: 'linear-gradient(135deg, #2d1b00 0%, #4a2c00 50%, #6b3f00 100%)',
    tense: 'linear-gradient(135deg, #1a0000 0%, #2d0a0a 50%, #3d1515 100%)',
    disoriented: 'linear-gradient(135deg, #1a1a2e 0%, #2e1a2e 50%, #1a2e1a 100%)',
    threatening: 'linear-gradient(135deg, #1a0000 0%, #330000 50%, #4d0000 100%)',
    formal: 'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 50%, #1a1a2e 100%)',
    ominous: 'linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0a1a1a 100%)',
    political: 'linear-gradient(135deg, #1a1a2e 0%, #2e1a1a 50%, #1a2e2e 100%)',
    epic: 'linear-gradient(135deg, #1a0a00 0%, #2e1a00 50%, #4d2a00 100%)',
    cosmic: 'linear-gradient(135deg, #0a001a 0%, #1a002e 50%, #0a0a2e 100%)',
    climactic: 'linear-gradient(135deg, #2e1a00 0%, #4d0a00 50%, #2e002e 100%)',
    hopeful: 'linear-gradient(135deg, #0a1a0a 0%, #1a2e1a 50%, #0a2e2e 100%)',
    serene: 'linear-gradient(135deg, #0a1a2e 0%, #1a2e3e 50%, #0a3e4e 100%)',
    dark: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 50%, #0a0a1a 100%)',
  };

  const LOCATION_GRADIENTS = {
    beach: 'linear-gradient(135deg, #1a365d 0%, #1e3a5f 50%, #2d3748 100%)',
    ship: 'linear-gradient(135deg, #1a365d 0%, #1e3a5f 50%, #2d3748 100%)',
    castle: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #1a1a3e 100%)',
    village: 'linear-gradient(135deg, #2d3a2d 0%, #1a2e1a 50%, #2d3a2d 100%)',
    temple: 'linear-gradient(135deg, #2e1a2e 0%, #1a162e 50%, #2e1a2e 100%)',
    market: 'linear-gradient(135deg, #2d2a1a 0%, #3e3a2a 50%, #2d2a1a 100%)',
    road: 'linear-gradient(135deg, #1a2e1a 0%, #2d3a2d 50%, #1a2a1a 100%)',
    battlefield: 'linear-gradient(135deg, #2e1a0a 0%, #3e1a0a 50%, #2e0a0a 100%)',
    garden: 'linear-gradient(135deg, #0a2e1a 0%, #1a3e2a 50%, #0a2e2e 100%)',
    court: 'linear-gradient(135deg, #2e1a1a 0%, #3e2a1a 50%, #2e1a2e 100%)',
  };

  // Story state
  let story = /** @type {any} */ (null);
  let voiceConfig = null;
  let loading = true;
  let error = null;

  // Navigation state
  let currentChapterIndex = 0;
  let currentPanelIndex = 0;

  // Game state
  let lives = 3;
  let livesTotal = 3;
  let score = 0;
  let choices = {};
  let gameOver = false;

  // Branching state
  let reputation = { diplomatic: 0, pragmatic: 0, bold: 0, hostile: 0, 'history-breaking': 0 };
  let branchHistory = [];     // [{ panelId, category, optionIndex }, ...]
  let pendingBranch = null;   // { next_panel, life_delta, reputation_delta }

  // Skeleton/segment state
  let storyLoader = null;
  let skeleton = null;
  let currentAnchorId = null;  // Which anchor we're currently in
  let segmentLoading = false;  // True when loading a new segment

  // Chapter transition & ending state
  let showChapterTransition = false;
  let chapterTransitionData = { title: '', number: 0, mood: 'tense' };
  let showLifeGain = false;
  let lifeGainReason = 'perfect';
  let showEnding = false;
  let prevChapterIndex = -1;  // For detecting chapter changes
  let bimboRepHint = null;    // { category, hint } - reputation personality comment

  // Interaction state
  let isTimeFrozen = false;
  let canAdvance = true;
  let isPlaying = false;
  let autoNarrate = loadAutoNarrate();
  let userHasInteracted = false;

  // Options/speaking state
  let previewedOption = null;
  let selectedOption = null;
  let requireRepeat = false;
  let speakResult = null;
  let liveTranscript = '';
  let draftText = '';
  let bimboHint = null;
  let askingBimbo = false;
  let bimboReaction = null;        // { bimboDialogue, teachingNote }
  let bimboReactionLoading = false;

  // Speech recognition state
  let isRecording = false;
  let mediaRecorder = null;
  let audioChunks = [];
  let recordingStream = null;
  let audioAnalyser = null;
  let evaluating = false;
  let streamingManager = null;

  // Menu state
  let menuVisible = false;

  // Dev tools ref + state
  let devToolsRef;
  let devAudioFile = null;
  let infiniteLives = false;

  // Audio engine
  let audioEngine = null;

  function loadAutoNarrate() {
    if (!browser) return true;
    try {
      const stored = localStorage.getItem(AUTO_NARRATE_KEY);
      if (stored !== null) return stored === 'true';
    } catch (_) {}
    return true;
  }

  $: storyId = $page.params.storyId;
  $: currentChapter = story?.chapters?.[currentChapterIndex];
  $: rawPanel = currentChapter?.panels?.[currentPanelIndex];
  $: currentPanel = resolvePanel(rawPanel, choices, branchHistory);
  // Total panels loaded so far (will grow as segments load)
  $: totalPanels = story?.chapters?.reduce((sum, ch) => sum + ch.panels.length, 0) || 0;
  // Estimated total from skeleton (for progress bar)
  $: estimatedTotalPanels = skeleton
    ? skeleton.anchors.length * 5  // ~5 panels per anchor as rough estimate
    : totalPanels;

  // Many anchors (esp. Bimbo's time-freeze/teaching panels) have no
  // generated panel art yet — `image` is null. Rather than show a bare
  // gradient while she's narrating, fall back to her illustrated character
  // reference (same portraits used elsewhere), like every other character
  // already gets via their panel art. A 404 (character with no reference,
  // e.g. lord_mori) just degrades to the gradient — background-image
  // failures paint nothing, no broken-image icon.
  $: fallbackCharacterImage = (() => {
    if (currentPanel?.image) return null;
    const speaker = currentPanel?.speaker;
    if (!speaker || speaker === 'player') return null;
    return `/images/generated/characters/${speaker}.png`;
  })();

  // Panel background: image + gradient overlay
  $: panelBg = (() => {
    const img = currentPanel?.image || fallbackCharacterImage;
    const grad = panelGradient;
    // Panel image now fills its aspect-matching frame container, so `cover`
    // is lossless (image aspect matches frame aspect per the backend's
    // panel_type → aspect map). The ambient blurred fullscreen layer is a
    // separate .panel-backdrop sibling; this is just the sharp hero image.
    if (img) return `url(${img}) center/cover no-repeat, ${grad}`;
    return grad;
  })();

  // Panel gradient based on mood/location
  $: panelGradient = (() => {
    const mood = currentPanel?.mood;
    const location = currentPanel?.location;
    if (mood && MOOD_GRADIENTS[mood]) return MOOD_GRADIENTS[mood];
    if (location && LOCATION_GRADIENTS[location]) return LOCATION_GRADIENTS[location];
    if (skeleton && currentAnchorId) {
      const anchor = skeleton.anchors?.find(a => a.id === currentAnchorId);
      if (anchor?.mood && MOOD_GRADIENTS[anchor.mood]) return MOOD_GRADIENTS[anchor.mood];
      if (anchor?.location && LOCATION_GRADIENTS[anchor.location]) return LOCATION_GRADIENTS[anchor.location];
    }
    return MOOD_GRADIENTS.dark;
  })();

  // Dominant reputation category (for ending screen)
  $: dominantCategory = (() => {
    let max = 0;
    let cat = 'pragmatic';
    for (const [k, v] of Object.entries(reputation)) {
      if (v > max) { max = v; cat = k; }
    }
    return cat;
  })();

  // Chapter change detection — show transition when advancing to a new chapter
  $: if (story && currentChapterIndex !== prevChapterIndex) {
    if (prevChapterIndex >= 0 && currentChapterIndex > prevChapterIndex) {
      const ch = story.chapters[currentChapterIndex];
      if (ch) {
        chapterTransitionData = {
          title: ch.title || '',
          number: currentChapterIndex + 1,
          mood: getMoodForCurrentAnchor(),
        };
        showChapterTransition = true;
        // +1 life on chapter complete (cap at 5)
        if (lives < 5) {
          lives = Math.min(5, lives + 1);
          livesTotal = Math.max(livesTotal, lives);
          lifeGainReason = 'chapter';
          showLifeGain = false;
          setTimeout(() => { showLifeGain = true; }, 50);
        }
      }
    }
    prevChapterIndex = currentChapterIndex;
  }

  function getMoodForCurrentAnchor() {
    if (!skeleton || !currentAnchorId) return 'tense';
    const anchor = skeleton.anchors?.find(a => a.id === currentAnchorId);
    return anchor?.mood || 'tense';
  }

  // Last panel only at the very end of the story (last chapter, last panel, no more anchors)
  $: isLastPanel = (() => {
    if (!story) return false;
    const atEndOfChapter = currentPanelIndex === (currentChapter?.panels?.length || 1) - 1;
    const atLastChapter = currentChapterIndex === (story?.chapters?.length || 1) - 1;
    // If skeleton exists, check if there are more anchors to load
    if (skeleton && storyLoader && currentAnchorId) {
      const nextAnchor = storyLoader.getNextAnchor(currentAnchorId);
      if (nextAnchor) return false; // More content available
    }
    return atEndOfChapter && atLastChapter;
  })();

  // Check if this panel has options (triggers time freeze game mechanic)
  $: hasOptions = currentPanel?.options?.length > 0;
  // Time freeze only triggers when there are options to speak
  $: hasTimeFreeze = hasOptions;

  // Format options for TimeStopPanel
  $: formattedOptions = (() => {
    if (!currentPanel?.options) return [];
    return currentPanel.options.map(o => ({
      option_text: o.text,
      style: o.style || null,
      next_scenario: o.next_scenario,
      examples: o.examples || []
    }));
  })();

  // Track panel changes
  let lastPanelId = null;
  $: if (currentPanel?.id && currentPanel.id !== lastPanelId) {
    lastPanelId = currentPanel.id;
    // Reset state on panel change
    previewedOption = null;
    selectedOption = null;
    requireRepeat = false;
    speakResult = null;
    liveTranscript = '';
    draftText = '';
    bimboHint = null;
    askingBimbo = false;
    bimboReaction = null;
    bimboReactionLoading = false;

    // Check if we should freeze time
    if (hasTimeFreeze && !isTimeFrozen) {
      triggerTimeFreeze();
      // Dev: auto-inject audio on freeze
      if (devToolsRef && devAudioFile) {
        devToolsRef.checkAutoInject(devAudioFile);
      }
    } else if (!hasTimeFreeze && isTimeFrozen) {
      resumeTime();
    }

    // Auto-narrate if enabled - play on ALL panels including time freeze
    if (autoNarrate && userHasInteracted && audioEngine) {
      setTimeout(() => audioEngine.autoPlayPanel(userHasInteracted), 100);
    }

    // Track current anchor based on current panel position
    if (skeleton && story) {
      updateCurrentAnchor();
    }
  }

  // Calculate progress
  $: currentPanelNumber = (() => {
    if (!story) return 0;
    let count = 0;
    for (let i = 0; i < currentChapterIndex; i++) {
      count += story.chapters[i].panels.length;
    }
    return count + currentPanelIndex + 1;
  })();

  $: progress = estimatedTotalPanels > 0 ? Math.min(100, (currentPanelNumber / estimatedTotalPanels) * 100) : 0;

  function jumpToPanel(panelId) {
    const loc = findPanelLocation(story, panelId);
    if (loc) {
      currentChapterIndex = loc.chapterIndex;
      currentPanelIndex = loc.panelIndex;
    } else {
      // Fallback: sequential advance
      console.warn(`[Branch] Panel "${panelId}" not found, advancing sequentially`);
      if (currentPanelIndex < currentChapter.panels.length - 1) {
        currentPanelIndex++;
      } else if (currentChapterIndex < story.chapters.length - 1) {
        currentChapterIndex++;
        currentPanelIndex = 0;
      }
    }
  }

  function stopAudio() {
    if (audioEngine) audioEngine.stopAudio();
  }

  function saveProgress() {
    if (!storyId) return;
    setJson(STORAGE_KEYS.STORY_PROGRESS, {
      storyId,
      chapterIndex: currentChapterIndex,
      panelIndex: currentPanelIndex,
      currentAnchorId,
      score,
      lives,
      livesTotal,
      choices,
      reputation,
      branchHistory,
      timestamp: Date.now(),
    });
  }

  async function loadProgress() {
    const saved = getJson(STORAGE_KEYS.STORY_PROGRESS, null);
    if (!saved || saved.storyId !== storyId) return;

    score = saved.score ?? 0;
    lives = saved.lives ?? 3;
    livesTotal = saved.livesTotal ?? 3;
    choices = saved.choices ?? {};
    reputation = saved.reputation ?? { diplomatic: 0, pragmatic: 0, bold: 0, hostile: 0, 'history-breaking': 0 };
    branchHistory = saved.branchHistory ?? [];
    if (lives <= 0) gameOver = true;

    // Restore anchor position
    if (saved.currentAnchorId) currentAnchorId = saved.currentAnchorId;

    // If saved chapter has panels, navigate directly
    const savedChIdx = saved.chapterIndex ?? 0;
    const savedPanelIdx = saved.panelIndex ?? 0;
    // Set prevChapterIndex to prevent chapter transition on restore
    prevChapterIndex = savedChIdx;
    if (story?.chapters?.[savedChIdx]?.panels?.length > savedPanelIdx) {
      currentChapterIndex = savedChIdx;
      currentPanelIndex = savedPanelIdx;
    } else if (saved.currentAnchorId && storyLoader && skeleton) {
      // Saved anchor is in a chapter without loaded panels — load the segment
      const firstNewIdx = await loadSegmentForAnchor(saved.currentAnchorId);
      const chapter = storyLoader.getChapterForAnchor(saved.currentAnchorId);
      if (chapter && story) {
        const chIdx = story.chapters.findIndex(ch => ch.id === chapter.id);
        if (chIdx >= 0) {
          currentChapterIndex = chIdx;
          currentPanelIndex = Math.min(savedPanelIdx, Math.max(0, story.chapters[chIdx].panels.length - 1));
        }
      }
    } else {
      currentChapterIndex = savedChIdx;
      currentPanelIndex = savedPanelIdx;
    }
  }

  function resetGame() {
    currentChapterIndex = 0;
    currentPanelIndex = 0;
    currentAnchorId = skeleton?.anchors?.[0]?.id || null;
    score = 0;
    lives = 3;
    livesTotal = 3;
    choices = {};
    reputation = { diplomatic: 0, pragmatic: 0, bold: 0, hostile: 0, 'history-breaking': 0 };
    branchHistory = [];
    pendingBranch = null;
    gameOver = false;
    isTimeFrozen = false;
    canAdvance = true;
    previewedOption = null;
    selectedOption = null;
    requireRepeat = false;
    speakResult = null;
    liveTranscript = '';
    draftText = '';
    bimboHint = null;
    askingBimbo = false;
    bimboReaction = null;
    bimboReactionLoading = false;
    bimboRepHint = null;
    resetBimboHints();
    stopAudio();
    cleanupRecording();
    saveProgress();
  }

  /**
   * Load a segment's panels into the story structure for the given anchor.
   * Returns the index of the first newly injected panel, or -1 if none.
   */
  async function loadSegmentForAnchor(anchorId) {
    if (!storyLoader || !skeleton) return -1;

    const nextAnchor = storyLoader.getNextAnchor(anchorId);
    if (!nextAnchor) return -1;

    segmentLoading = true;
    try {
      const result = await storyLoader.loadSegment(anchorId, nextAnchor.id, {
        reputation,
        branch_history: branchHistory,
        lives,
      });

      if (result.panels?.length > 0) {
        // Find the chapter for this anchor
        const chapter = storyLoader.getChapterForAnchor(anchorId);
        if (chapter && story) {
          const storyChapter = story.chapters.find(ch => ch.id === chapter.id);
          if (storyChapter) {
            const existingIds = new Set(storyChapter.panels.map(p => p.id));
            const newPanels = result.panels.filter(p => !existingIds.has(p.id));
            if (newPanels.length > 0) {
              const firstNewIdx = storyChapter.panels.length;
              storyChapter.panels = [...storyChapter.panels, ...newPanels];
              story = story; // trigger reactivity
              return firstNewIdx;
            }
          }
        }
      }
      return -1;
    } catch (e) {
      console.warn('[StoryLoader] Failed to load segment:', e);
      return -1;
    } finally {
      segmentLoading = false;
    }
  }

  /**
   * Trigger prefetch when ~80% through current segment.
   */
  function checkPrefetch() {
    if (!storyLoader || !currentAnchorId) return;
    storyLoader.prefetchNext(currentAnchorId, {
      reputation,
      branch_history: branchHistory,
      lives,
    });
  }

  /**
   * Update currentAnchorId based on which chapter/panel we're viewing.
   * Also triggers prefetch when near end of chapter.
   */
  function updateCurrentAnchor() {
    if (!skeleton || !story || !currentChapter) return;

    // Find which anchor we're in by matching chapter ID
    const chapterId = currentChapter.id;
    const chapterDef = skeleton.chapters?.find(ch => ch.id === chapterId);
    if (!chapterDef) return;

    // Use the last anchor of this chapter's anchor list as a conservative guess
    // (panels flow through anchors sequentially within a chapter)
    const anchorIds = chapterDef.anchor_ids || [];
    if (anchorIds.length > 0) {
      // Simple: use the chapter's last anchor (we've loaded all of them)
      const lastAnchor = anchorIds[anchorIds.length - 1];
      if (currentAnchorId !== lastAnchor) {
        currentAnchorId = lastAnchor;
      }
    }

    // Prefetch when near end of chapter panels
    if (currentChapter.panels?.length > 0) {
      const progress = (currentPanelIndex + 1) / currentChapter.panels.length;
      if (progress >= 0.8) {
        checkPrefetch();
      }
    }
  }

  /**
   * Advance to the next segment/anchor. Loads panels and navigates.
   * Returns true if navigation happened.
   */
  async function advanceToNextSegment() {
    if (!storyLoader || !currentAnchorId) return false;

    // Find the next anchor
    let nextAnchorId = null;
    const anchor = skeleton?.anchors?.find(a => a.id === currentAnchorId);

    // Handle reputation gates
    if (anchor?.type === 'reputation_gate' && anchor.gate_config) {
      nextAnchorId = storyLoader.resolveGate(currentAnchorId, reputation);
    }

    if (!nextAnchorId) {
      const nextAnchor = storyLoader.getNextAnchor(currentAnchorId);
      if (!nextAnchor) return false;
      nextAnchorId = nextAnchor.id;
    }

    // Check if next anchor is itself a gate (gates may have no panels)
    const nextAnchorObj = skeleton?.anchors?.find(a => a.id === nextAnchorId);
    if (nextAnchorObj?.type === 'reputation_gate' && nextAnchorObj.gate_config) {
      currentAnchorId = nextAnchorId;
      return advanceToNextSegment(); // Recurse through gate
    }

    currentAnchorId = nextAnchorId;

    // Try to find the anchor's panels already in the story
    const chapter = storyLoader.getChapterForAnchor(nextAnchorId);
    if (chapter && story) {
      const chIdx = story.chapters.findIndex(ch => ch.id === chapter.id);
      const storyChapter = story.chapters[chIdx];

      if (storyChapter && storyChapter.panels.length > 0) {
        // Panels already loaded — navigate to first panel of this chapter
        // (or find the specific anchor's first panel)
        currentChapterIndex = chIdx;
        currentPanelIndex = 0;
        saveProgress();
        return true;
      }
    }

    // Panels not loaded — fetch segment
    const firstNewIdx = await loadSegmentForAnchor(nextAnchorId);
    if (firstNewIdx >= 0 && chapter && story) {
      const chIdx = story.chapters.findIndex(ch => ch.id === chapter.id);
      if (chIdx >= 0) {
        currentChapterIndex = chIdx;
        currentPanelIndex = firstNewIdx;
        saveProgress();
        return true;
      }
    }

    // Even if segment returned placeholder, navigate to that chapter
    if (chapter && story) {
      const chIdx = story.chapters.findIndex(ch => ch.id === chapter.id);
      if (chIdx >= 0 && story.chapters[chIdx].panels.length > 0) {
        currentChapterIndex = chIdx;
        currentPanelIndex = 0;
        saveProgress();
        return true;
      }
    }

    return false;
  }

  onMount(async () => {
    autoNarrate = loadAutoNarrate();

    // Create audio engine
    audioEngine = createAudioEngine({
      getPanel: () => currentPanel,
      onPlayingChange: (v) => { isPlaying = v; },
    });

    try {
      // Load story data and skeleton in parallel
      storyLoader = createStoryLoader(storyId, { language: narrationLanguage, level: narrationLevel });

      const [storyRes, voiceRes, skeletonResult] = await Promise.all([
        fetch(`${API_BASE}/api/story-panels/stories/${storyId}${storyFetchQuery()}`),
        fetch(`${API_BASE}/api/story-panels/stories/${storyId}/voice-config`),
        storyLoader.loadSkeleton().catch(() => null),
      ]);

      if (!storyRes.ok) throw new Error('Story not found');
      story = await storyRes.json();

      if (voiceRes.ok) {
        voiceConfig = await voiceRes.json();
      }

      // Store skeleton if loaded and set per-story categories
      if (skeletonResult) {
        skeleton = skeletonResult;
        const { categories, styleToCategory } = buildCategoriesFromSkeleton(skeleton);
        setActiveCategories(categories, styleToCategory);
        // Set initial anchor to first anchor
        if (skeleton.anchors?.length > 0) {
          currentAnchorId = skeleton.anchors[0].id;
        }
      }

      // Restore saved progress after story loads
      await loadProgress();
      // Ensure prevChapterIndex is synced so chapter transition doesn't fire
      prevChapterIndex = currentChapterIndex;
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  });

  onDestroy(() => {
    if (audioEngine) audioEngine.destroy();
    cleanupRecording();
    if (streamingManager) {
      streamingManager.close();
    }
    if (devToolsRef) devToolsRef.cleanup();
  });

  // Fetch dynamic Bimbo reaction after player speaks
  async function fetchBimboReaction(result, panel, categoryKey) {
    bimboReaction = null;
    bimboReactionLoading = true;
    try {
      const matchedIdx = result.matched_index ?? -1;
      const matchedOpt = (matchedIdx >= 0 && panel?.options) ? panel.options[matchedIdx] : null;
      const body = {
        heard: result.heard || '',
        heard_translation: result.heard_translation || '',
        tier: result.tier || 'fail',
        match_level: result.match_level ?? 0,
        matched_index: matchedIdx,
        category: categoryKey || '',
        matched_option: matchedOpt ? { text: matchedOpt.text, style: matchedOpt.style || '', target: matchedOpt.examples?.[0]?.target || '' } : null,
        all_options: (panel?.options || []).map(o => ({ text: o.text, style: o.style || '', target: o.examples?.[0]?.target || '' })),
        panel_dialogue: panel?.dialogue || '',
        scene_context: panel?.narration?.slice(0, 200) || '',
      };
      const resp = await fetch(`${API_BASE}/narrative/generate-reaction`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (resp.ok) {
        const data = await resp.json();
        if (data.bimbo_dialogue) {
          bimboReaction = { bimboDialogue: data.bimbo_dialogue, teachingNote: data.teaching_note || '' };
        }
      }
    } catch (e) {
      console.warn('[BimboReaction] fetch failed:', e);
    } finally {
      bimboReactionLoading = false;
    }
  }

  // Initialize streaming manager for speech recognition
  function initStreamingManager() {
    if (streamingManager) return;

    streamingManager = createStreamingManager({
      getScenario: () => {
        if (currentPanel?.options?.length > 0) {
          const targets = currentPanel.options
            .map(o => o.examples?.[0]?.target)
            .filter(Boolean);
          if (targets.length > 0) {
            return { id: null, expected_responses: targets };
          }
        }
        return null;
      },
      getLanguage: () => skeleton?.target_language || 'Japanese',
      getGameState: () => ({ score, lives, livesTotal, judgeFocus: 0 }),
      onStateUpdate: () => {},
      onTranscript: (text, partial) => {
        liveTranscript = text;
        if (partial?.detected_language && devToolsRef) devToolsRef.setDevLastLang(partial.detected_language);
      },
      onResult: (result) => {
        console.log('[Speech] Result:', result);
        if (devToolsRef) devToolsRef.setDevLastResult(result);
        isRecording = false;
        evaluating = false;
        clearSpeechWatchdog();
        cleanupRecording();

        const matchLevel = result.match_level ?? 0;
        const tier = result.tier || (matchLevel >= 0.7 ? 'good' : 'fail');

        // Silence — nothing was heard, just reset so they can try again
        if (tier === 'silence') {
          speakResult = { success: false, message: "Didn't catch anything — try again", silence: true };
          return;
        }

        // Record matched option for all non-fail tiers
        if (tier !== 'fail') {
          const matchedIdx = result.matched_index;
          if (matchedIdx !== undefined && matchedIdx >= 0 && currentPanel?.options) {
            const matchedOpt = currentPanel.options[matchedIdx];
            if (matchedOpt) {
              choices = { ...choices, [currentPanel.id]: matchedIdx };
              selectedOption = { example: matchedOpt.examples?.[0] };
            }
          }
        }

        // Resolve branch for any non-silence tier
        const branchMatchedIdx = result.matched_index;
        const branchMatchedOpt = (branchMatchedIdx >= 0 && currentPanel?.options) ? currentPanel.options[branchMatchedIdx] : null;
        const branchCategoryKey = branchMatchedOpt ? getCategoryKey(branchMatchedOpt) : 'pragmatic';

        const outcome = resolveBranch(currentPanel, branchMatchedIdx, branchCategoryKey);
        if (outcome) {
          if (outcome.reputation_delta) {
            for (const [cat, delta] of Object.entries(outcome.reputation_delta)) {
              reputation[cat] = (reputation[cat] || 0) + delta;
            }
            reputation = reputation; // trigger reactivity
            // Check for Bimbo reputation hint
            const repHint = checkBimboHint(reputation);
            if (repHint) {
              bimboRepHint = repHint;
              setTimeout(() => { bimboRepHint = null; }, 6000);
            }
          }
          if (outcome.life_delta && outcome.life_delta < 0 && !infiniteLives) {
            lives = Math.max(0, lives + outcome.life_delta);
            if (lives <= 0) gameOver = true;
          }
          branchHistory = [...branchHistory, { panelId: currentPanel.id, category: branchCategoryKey, optionIndex: branchMatchedIdx }];
          pendingBranch = outcome;
        }

        // Fire async Bimbo reaction for panels with options
        if (currentPanel?.options?.length > 0) {
          fetchBimboReaction(result, currentPanel, branchCategoryKey);
        }

        if (tier === 'perfect' || tier === 'good') {
          const quality = tier === 'perfect' ? 'Perfect!' : matchLevel >= 0.8 ? 'Great!' : 'Good!';
          const matchedIdx = result.matched_index;
          const matchedOpt = (matchedIdx >= 0 && currentPanel?.options) ? currentPanel.options[matchedIdx] : null;
          const category = matchedOpt ? getOptionCategory(matchedOpt) : null;
          speakResult = { success: true, message: quality, tier, heard: result.heard || '', heardTranslation: result.heard_translation || '', heardPronunciation: result.heard_pronunciation || '', category };
          score += Math.round(matchLevel * 100);

          // Life recovery: +1 on perfect speech match (cap at 5)
          if (tier === 'perfect' && lives < 5 && !infiniteLives) {
            lives = Math.min(5, lives + 1);
            livesTotal = Math.max(livesTotal, lives);
            lifeGainReason = 'perfect';
            showLifeGain = false;
            setTimeout(() => { showLifeGain = true; }, 50);
          }

          playBeep({ frequency: 880, duration: 200 });
          saveProgress();

        } else {
          const heard = result.heard || '';
          const heardTranslation = result.heard_translation || '';
          const heardPronunciation = result.heard_pronunciation || '';

          const matchedIdx = result.matched_index;
          const matchedOpt = (matchedIdx >= 0 && currentPanel?.options) ? currentPanel.options[matchedIdx] : null;
          const category = matchedOpt ? getOptionCategory(matchedOpt) : null;

          speakResult = { success: false, tier, heard, heardTranslation, heardPronunciation, category, canSkip: true };
          requireRepeat = true;

          saveProgress();
          playBeep({ frequency: 420, duration: 160 });
        }
      },
      onPenalty: (data) => {
        console.log('[Speech] Penalty:', data);
        const lang = skeleton?.target_language || 'Spanish';
        speakResult = { success: false, message: data.message || `Prueba de nuevo en ${lang === 'Spanish' ? 'español' : lang}` };
        isRecording = false;
        evaluating = false;
        clearSpeechWatchdog();
        cleanupRecording();
      },
      onError: (err) => {
        console.error('[Speech] Error:', err);
        speakResult = { success: false, message: t('connection_error', uiLang) };
        isRecording = false;
        evaluating = false;
        clearSpeechWatchdog();
        cleanupRecording();
      },
    });
  }

  // Live mic-level driven by the AudioAnalyser. Updated by rAF, read by the UI.
  // Uses the TIME-DOMAIN waveform (getByteTimeDomainData) rather than the
  // frequency-domain data because time-domain reads reliably as soon as the
  // mediaStreamSource is connected, while frequency-domain tends to stay zero
  // on mobile browsers if the AudioContext hasn't fully resumed yet.
  let micLevel = 0;              // 0..1 perceptual
  let micLevelRaw = 0;           // raw RMS for debugging
  let micLevelRAF = null;
  function startMicLevelLoop() {
    stopMicLevelLoop();
    if (!audioAnalyser) {
      console.warn('[Mic] startMicLevelLoop: no audioAnalyser');
      return;
    }
    const buf = new Uint8Array(audioAnalyser.fftSize);
    const tick = () => {
      if (!isRecording || !audioAnalyser) {
        micLevel = 0;
        micLevelRaw = 0;
        micLevelRAF = null;
        return;
      }
      audioAnalyser.getByteTimeDomainData(buf);
      // Time-domain samples sit around 128 (silence = DC center). RMS of the
      // deviation gives us a true volume estimate independent of pitch.
      let sumSq = 0;
      for (let i = 0; i < buf.length; i++) {
        const v = (buf[i] - 128) / 128;      // -1..1
        sumSq += v * v;
      }
      const rms = Math.sqrt(sumSq / buf.length);  // 0..~0.3 for normal speech
      micLevelRaw = rms;
      // Perceptual curve so a normal-volume voice reads around 0.5-0.8
      micLevel = Math.min(1, Math.pow(Math.min(1, rms * 4.5), 0.6));
      // Push raw level to the DevTools panel for debugging (hidden from the game UI).
      if (devToolsRef?.setDevMicLevel) devToolsRef.setDevMicLevel(rms);
      micLevelRAF = requestAnimationFrame(tick);
    };
    micLevelRAF = requestAnimationFrame(tick);
  }
  function stopMicLevelLoop() {
    if (micLevelRAF) { cancelAnimationFrame(micLevelRAF); micLevelRAF = null; }
    micLevel = 0;
    micLevelRaw = 0;
  }

  // Watchdog: if the backend never emits a final/penalty/error event within
  // 20 s of a stop signal, surface it to the user instead of spinning forever.
  let speechWatchdog = null;
  function startSpeechWatchdog() {
    clearSpeechWatchdog();
    speechWatchdog = setTimeout(() => {
      if (evaluating) {
        console.warn('[Speech] watchdog fired — no response from backend');
        speakResult = { success: false, message: t('no_server_response', uiLang), canSkip: true };
        isRecording = false;
        evaluating = false;
        cleanupRecording();
      }
    }, 20000);
  }
  function clearSpeechWatchdog() {
    if (speechWatchdog) { clearTimeout(speechWatchdog); speechWatchdog = null; }
  }

  // iOS-safe mic flow — ported from llmTerminal/web/public/app-voice.js, which
  // runs successfully on iPhone Safari day in / day out. KEY RULES:
  //   1. Use navigator.mediaDevices.getUserMedia(...).then(stream => ...) —
  //      NOT await — because iOS requires the gesture-scoped microtask chain
  //      to stay intact for the AudioContext creation that follows.
  //   2. Create a FRESH AudioContext inside the .then handler. Do NOT reuse a
  //      cached one — iOS leaves suspended contexts suspended even inside a
  //      gesture if they were created earlier.
  //   3. new MediaRecorder(stream) — no mimeType. Safari rejects
  //      'audio/webm;codecs=opus' and silently fails.
  //   4. mediaRecorder.start() — no timeslice. Safari emits malformed chunks
  //      otherwise. One 'dataavailable' fires at stop() with the full blob.
  //   5. Build the Blob with voiceRec.mimeType (iOS gives audio/mp4).
  //   6. Discard sub-1 KB blobs — iOS sometimes finalizes empty on fast stops.

  // Analyser kept at module scope so stopMicLevelLoop and cleanupRecording
  // can tear it down independent of whether MediaRecorder is still alive.
  let micAudioCtx = null;
  let micMeterSource = null;

  function stopMicMeter() {
    stopMicLevelLoop();
    try { micMeterSource?.disconnect?.(); } catch (_) {}
    micMeterSource = null;
    audioAnalyser = null;
    if (micAudioCtx && micAudioCtx.state !== 'closed') {
      try { micAudioCtx.close(); } catch (_) {}
    }
    micAudioCtx = null;
  }

  function toggleRecording() {
    if (isRecording) {
      // Stop: delegates to mediaRecorder.onstop which builds the blob + sends.
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        try { mediaRecorder.stop(); } catch (_) {}
      }
      isRecording = false;
      evaluating = true;
      startSpeechWatchdog();
      stopMicMeter();
      return;
    }

    userHasInteracted = true;
    stopAudio();

    // Reset the UI *synchronously* so the red banner appears before the
    // getUserMedia prompt (iOS shows a permission sheet; the user needs to
    // see we're asking for mic).
    liveTranscript = '';
    speakResult = null;
    bimboReaction = null;
    bimboReactionLoading = false;
    if (devToolsRef?.resetDevMic) devToolsRef.resetDevMic();

    // Recreate the streaming manager up-front, synchronously, so it's ready
    // when onstop fires. getScenario / getLanguage capture the current panel.
    if (streamingManager) {
      try { streamingManager.close(); } catch (_) {}
      streamingManager = null;
    }
    initStreamingManager();
    streamingManager.setEnabled(true);
    streamingManager.connect();

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      speakResult = { success: false, message: t('voice_unsupported', uiLang) };
      return;
    }

    navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
      recordingStream = stream;
      try {
        const t = stream.getAudioTracks?.()[0];
        console.log('[Mic] stream track:', t && { enabled: t.enabled, muted: t.muted, readyState: t.readyState, label: (t.label || '').slice(0, 60) });
      } catch (_) {}

      // Build a FRESH AudioContext right here, inside the .then — iOS keeps
      // the gesture pass alive through this microtask. A fresh context starts
      // in 'running' on iOS when created inside a gesture; a cached one does not.
      try {
        const Ctx = window.AudioContext || window.webkitAudioContext;
        micAudioCtx = new Ctx();
        const src = micAudioCtx.createMediaStreamSource(stream);
        const analyser = micAudioCtx.createAnalyser();
        analyser.fftSize = 1024;
        analyser.smoothingTimeConstant = 0.6;
        src.connect(analyser);
        micMeterSource = src;
        audioAnalyser = analyser;
        if (devToolsRef?.setDevMicCtxState) devToolsRef.setDevMicCtxState(micAudioCtx.state);
        console.log('[Mic] fresh AudioContext state:', micAudioCtx.state, 'sampleRate:', micAudioCtx.sampleRate);
        // Smoke test
        try {
          const buf = new Uint8Array(analyser.fftSize);
          analyser.getByteTimeDomainData(buf);
          let maxDev = 0;
          for (let i = 0; i < buf.length; i++) { const d = Math.abs(buf[i] - 128); if (d > maxDev) maxDev = d; }
          if (devToolsRef?.setDevMicFirstFrame) devToolsRef.setDevMicFirstFrame(maxDev);
          console.log('[Mic] first-frame max deviation:', maxDev);
        } catch (_) {}
      } catch (err) {
        console.warn('[Mic] AudioContext setup failed (meter will be dead but recording continues):', err);
      }

      // MediaRecorder — no mimeType, no timeslice.
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e?.data && e.data.size > 0) audioChunks.push(e.data);
      };
      mediaRecorder.onerror = (e) => {
        console.error('[Mic] MediaRecorder error:', e);
        try { stream.getTracks().forEach(t => t.stop()); } catch (_) {}
        speakResult = { success: false, message: t('recording_error', uiLang) };
        isRecording = false;
        evaluating = false;
        clearSpeechWatchdog();
        stopMicMeter();
      };
      mediaRecorder.onstop = () => {
        try { stream.getTracks().forEach(t => t.stop()); } catch (_) {}
        recordingStream = null;

        const actualMime = mediaRecorder.mimeType || 'audio/mp4';
        const blob = new Blob(audioChunks, { type: actualMime });
        audioChunks = [];
        console.log('[Mic] stop → blob:', blob.size, 'bytes, type=', blob.type);

        if (blob.size < 1000) {
          console.warn('[Mic] blob too small, discarding');
          speakResult = { success: false, message: t('recording_too_short', uiLang), silence: true };
          isRecording = false;
          evaluating = false;
          clearSpeechWatchdog();
          stopMicMeter();
          return;
        }

        // Send the single consolidated blob + mime hint + stop.
        (async () => {
          try {
            if (streamingManager) {
              await streamingManager.sendMimeType(blob.type);
              await streamingManager.sendChunk(blob);
              streamingManager.signalStop('stop');
            }
          } catch (err) {
            console.error('[Mic] send failed:', err);
            speakResult = { success: false, message: t('send_error', uiLang) };
            isRecording = false;
            evaluating = false;
            clearSpeechWatchdog();
          }
        })();
      };

      mediaRecorder.start();  // no timeslice
      isRecording = true;
      startMicLevelLoop();
    }).catch((err) => {
      logMicError(err);
      if (err && err.name === 'NotAllowedError') {
        speakResult = { success: false, message: t('mic_denied', uiLang) };
      } else {
        speakResult = { success: false, message: t('mic_unavailable', uiLang) };
      }
    });
  }

  const _micErrorLastLogged = new Map();
  function logMicError(err) {
    const key = String(err?.name || err?.message || 'unknown');
    const now = Date.now();
    const last = _micErrorLastLogged.get(key) || 0;
    if (now - last < 60000) return;  // 1 per minute per error class
    _micErrorLastLogged.set(key, now);
    console.error('Error accessing microphone:', err);
  }

  async function injectAudio() {
    if (!devAudioFile) return;

    stopAudio();
    if (streamingManager) {
      streamingManager.close();
      streamingManager = null;
    }
    initStreamingManager();

    liveTranscript = '';
    speakResult = null;
    bimboReaction = null;
    bimboReactionLoading = false;
    evaluating = true;

    streamingManager.setEnabled(true);
    streamingManager.connect();

    // Wait for WebSocket to open
    await new Promise(resolve => {
      const unsub = streamingManager.status.subscribe(s => {
        if (s === 'open') { unsub(); resolve(); }
      });
    });

    // Send the file as a single chunk
    const blob = devAudioFile.slice();
    await streamingManager.sendChunk(blob);

    // Brief pause then signal stop to trigger finalization
    await new Promise(r => setTimeout(r, 200));
    streamingManager.signalStop('stop');
  }

  function cleanupRecording() {
    stopMicMeter();
    if (recordingStream) {
      try {
        recordingStream.getTracks().forEach(t => t.stop());
      } catch (_) {}
      recordingStream = null;
    }
    if (streamingManager) {
      streamingManager.setEnabled(false);
    }
    disconnectAnalyser();
    liveTranscript = '';
  }

  function triggerTimeFreeze() {
    cleanupRecording();
    isTimeFrozen = true;
    canAdvance = false;
  }

  function resumeTime() {
    isTimeFrozen = false;
    canAdvance = true;
    previewedOption = null;
    selectedOption = null;
    requireRepeat = false;
  }

  function handleOptionPreview(event) {
    const detail = event?.detail || {};
    previewedOption = detail;
    speakResult = null;
    if (audioEngine) audioEngine.playExample(detail.example);
  }

  async function handleAskBimbo(event) {
    const text = event?.detail;
    console.log('[AskBimbo] Triggered, text:', text);
    if (!text || askingBimbo) {
      console.log('[AskBimbo] Skipped — empty text or already asking');
      return;
    }

    askingBimbo = true;
    bimboHint = null;

    try {
      const optionsPayload = formattedOptions.map(o => ({
        text: o.option_text,
        style: o.style || '',
      }));
      console.log('[AskBimbo] Sending request:', { player_text: text, options: optionsPayload });

      const res = await fetch(`${API_BASE}/narrative/ask-bimbo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_text: text, options: optionsPayload }),
      });

      console.log('[AskBimbo] HTTP status:', res.status);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      console.log('[AskBimbo] Response data:', data);

      bimboHint = {
        matchedIndex: data.matched_index,
        confidence: data.confidence,
        bimboSays: data.bimbo_says,
        translation: data.translation || '',
        pronunciation: data.pronunciation || '',
        playerText: text,
      };
      console.log('[AskBimbo] bimboHint set:', bimboHint);

      // Auto-play translation audio if available
      if (data.translation) {
        console.log('[AskBimbo] Auto-playing translation:', data.translation);
        if (audioEngine) audioEngine.playExample({ target: data.translation });
      }
      // Also highlight matched option if one fits
      else if (data.matched_index >= 0 && formattedOptions[data.matched_index]) {
        const matchedOpt = formattedOptions[data.matched_index];
        console.log('[AskBimbo] Auto-previewing matched option:', data.matched_index, matchedOpt.option_text);
        if (matchedOpt.examples?.[0]) {
          if (audioEngine) audioEngine.playExample(matchedOpt.examples[0]);
        }
      } else {
        console.log('[AskBimbo] No option to auto-preview (index:', data.matched_index, ')');
      }
    } catch (err) {
      console.error('[AskBimbo] Error:', err);
      bimboHint = {
        matchedIndex: -1,
        confidence: 'none',
        bimboSays: "Hmm, I'm having trouble thinking right now. Try tapping an option to hear it!",
        translation: '',
        pronunciation: '',
        playerText: text,
      };
    } finally {
      askingBimbo = false;
      console.log('[AskBimbo] Done. askingBimbo=false, bimboHint:', bimboHint);
    }
  }

  function handlePlayBimboTranslation(event) {
    const detail = event?.detail;
    if (detail?.target && audioEngine) {
      audioEngine.playExample({ target: detail.target });
    }
  }

  function handlePlayAudio() {
    if (selectedOption?.example && audioEngine) {
      audioEngine.playExample(selectedOption.example);
    }
  }

  function handleChapterContinue() {
    showChapterTransition = false;
  }

  function handlePlayAgain() {
    showEnding = false;
    resetGame();
  }

  function handleFinishStory() {
    showEnding = true;
  }

  function handleSpeakResultContinue() {
    speakResult = null;
    bimboReaction = null;
    bimboReactionLoading = false;
    requireRepeat = false;
    resumeTime();
    nextPanel();
  }

  function nextPanel() {
    if (!canAdvance || isTimeFrozen) return;

    // Any Next click counts as user interaction — needed to unlock the
    // browser's autoplay policy for TTS narration. Previously only
    // handleKeydown / handlePanelClick set this, so clicking the Next
    // button alone left auto-narrate permanently gated.
    userHasInteracted = true;

    stopAudio();

    if (pendingBranch?.next_panel) {
      const targetId = pendingBranch.next_panel;
      pendingBranch = null;
      jumpToPanel(targetId);
    } else if (currentPanel?.next_panel) {
      jumpToPanel(currentPanel.next_panel);
    } else {
      // Normal sequential advance
      if (currentPanelIndex < currentChapter.panels.length - 1) {
        currentPanelIndex++;
      } else if (currentChapterIndex < story.chapters.length - 1) {
        // Check if next chapter has panels
        const nextCh = story.chapters[currentChapterIndex + 1];
        if (nextCh && nextCh.panels.length > 0) {
          currentChapterIndex++;
          currentPanelIndex = 0;
        } else if (skeleton && storyLoader) {
          // Next chapter is empty — load next segment from skeleton
          advanceToNextSegment();
          return; // advanceToNextSegment handles navigation
        } else {
          // No skeleton — just advance anyway (will show empty)
          currentChapterIndex++;
          currentPanelIndex = 0;
        }
      }
    }
    saveProgress();
  }

  function prevPanel() {
    userHasInteracted = true;
    stopAudio();
    isTimeFrozen = false;
    canAdvance = true;
    selectedOption = null;
    requireRepeat = false;

    if (currentPanelIndex > 0) {
      currentPanelIndex--;
    } else if (currentChapterIndex > 0) {
      currentChapterIndex--;
      currentPanelIndex = story.chapters[currentChapterIndex].panels.length - 1;
    }
  }

  function toggleAutoNarrate() {
    autoNarrate = !autoNarrate;
    if (browser) {
      try { localStorage.setItem(AUTO_NARRATE_KEY, String(autoNarrate)); } catch (_) {}
    }
    if (autoNarrate && !isPlaying && !isTimeFrozen && audioEngine) {
      audioEngine.autoPlayPanel(userHasInteracted);
    } else if (!autoNarrate) {
      stopAudio();
    }
  }

  function openMenu() { menuVisible = true; }
  function closeMenu() { menuVisible = false; }
  function handleMenuExit() { menuVisible = false; window.location.href = '/'; }

  function handleKeydown(e) {
    const tag = document.activeElement?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;

    const wasInteracted = userHasInteracted;
    userHasInteracted = true;

    if (!wasInteracted && autoNarrate && audioEngine) {
      audioEngine.autoPlayPanel(userHasInteracted);
    }

    if (e.key === 'Escape') {
      if (menuVisible) closeMenu();
      else openMenu();
      return;
    }

    if (e.key === 'ArrowRight' || e.key === ' ') {
      e.preventDefault();
      if (isTimeFrozen && hasOptions) {
        toggleRecording();
      } else if (!isTimeFrozen) {
        nextPanel();
      }
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      prevPanel();
    }
  }

  function handlePanelClick(e) {
    const wasInteracted = userHasInteracted;
    userHasInteracted = true;

    if (!wasInteracted && autoNarrate && audioEngine) {
      audioEngine.autoPlayPanel(userHasInteracted);
    }

    if (isTimeFrozen) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    if (x > rect.width / 2) {
      nextPanel();
    } else {
      prevPanel();
    }
  }

  // DevTools event handlers
  function handleDevJumpToPanel(e) {
    const { chapterIdx, panelIdx, clearBranch } = e.detail;
    stopAudio();
    cleanupRecording();
    isTimeFrozen = false;
    canAdvance = true;
    previewedOption = null;
    selectedOption = null;
    requireRepeat = false;
    speakResult = null;
    bimboReaction = null;
    bimboReactionLoading = false;
    liveTranscript = '';
    if (clearBranch) {
      pendingBranch = null;
    }
    currentChapterIndex = chapterIdx;
    currentPanelIndex = panelIdx;
    saveProgress();
  }

  function handleDevForceCategory(e) {
    const categoryKey = e.detail;
    if (!currentPanel?.category_outcomes?.[categoryKey]) return;
    const outcome = currentPanel.category_outcomes[categoryKey];

    let matchedIdx = -1;
    if (currentPanel.options) {
      matchedIdx = currentPanel.options.findIndex(o => getCategoryKey(o) === categoryKey);
      if (matchedIdx < 0) matchedIdx = 0;
    }
    const matchedOpt = matchedIdx >= 0 ? currentPanel.options[matchedIdx] : null;

    if (matchedOpt) {
      choices = { ...choices, [currentPanel.id]: matchedIdx };
      selectedOption = { example: matchedOpt.examples?.[0] };
    }

    if (outcome.reputation_delta) {
      for (const [cat, delta] of Object.entries(outcome.reputation_delta)) {
        reputation[cat] = (reputation[cat] || 0) + delta;
      }
      reputation = reputation;
    }
    if (outcome.life_delta && outcome.life_delta < 0 && !infiniteLives) {
      lives = Math.max(0, lives + outcome.life_delta);
      if (lives <= 0) gameOver = true;
    }
    branchHistory = [...branchHistory, { panelId: currentPanel.id, category: categoryKey, optionIndex: matchedIdx }];
    pendingBranch = outcome;

    const catInfo = RESPONSE_CATEGORIES[categoryKey] || null;
    const heardText = matchedOpt?.examples?.[0]?.target || matchedOpt?.text || '';
    speakResult = {
      success: true,
      message: `Forced: ${categoryKey}`,
      tier: 'good',
      heard: heardText,
      heardTranslation: matchedOpt?.examples?.[0]?.reading || '',
      heardPronunciation: '',
      category: catInfo,
    };

    if (currentPanel.options?.length > 0) {
      fetchBimboReaction({
        heard: heardText,
        heard_translation: matchedOpt?.examples?.[0]?.reading || '',
        tier: 'good',
        match_level: 0.95,
        matched_index: matchedIdx,
      }, currentPanel, categoryKey);
    }

    saveProgress();
  }

  function handleDevResetReputation() {
    reputation = { diplomatic: 0, pragmatic: 0, bold: 0, hostile: 0, 'history-breaking': 0 };
    saveProgress();
  }

  function handleDevClearBranchHistory() {
    branchHistory = [];
    saveProgress();
  }

  function handleDevClearPendingBranch() {
    pendingBranch = null;
  }

  function handleDevAudioFileChange(e) {
    devAudioFile = e.detail;
  }

  function handleDevInfiniteLives(e) {
    infiniteLives = e.detail;
  }
  $: pageTitle = story?.title && currentChapter?.title
    ? `${story.title} — ${currentChapter.title} · LangHero`
    : story?.title
      ? `${story.title} · LangHero`
      : 'Playing · LangHero';
</script>

<svelte:head>
  <title>{pageTitle}</title>
</svelte:head>

<svelte:window on:keydown={handleKeydown} />

<GameMenu
  visible={menuVisible}
  judgeFocus={0}
  languageOverride=""
  micDevices={[]}
  micDeviceId=""
  scenariosCompleted={0}
  {narrationLanguage}
  {narrationLevel}
  on:close={closeMenu}
  on:exit={handleMenuExit}
  on:updateNarrationLanguage={handleUpdateNarrationLanguage}
  on:updateNarrationLevel={handleUpdateNarrationLevel}
/>

<div class="player" class:time-frozen={isTimeFrozen}>
  {#if loading}
    <div class="loading">
      <div class="loading-spinner"></div>
      <p>{t('loading_story', narrationLanguage)}</p>
    </div>
  {:else if error}
    <div class="error">{error}</div>
  {:else if story}
    <!-- HUD -->
    <GameHUD {lives} {livesTotal} {score} on:openMenu={openMenu} />

    <!-- Segment Loading Overlay -->
    {#if segmentLoading}
      <SegmentLoading />
    {/if}

    <!-- Chapter Transition -->
    {#if showChapterTransition}
      <ChapterTransition
        chapterTitle={chapterTransitionData.title}
        chapterNumber={chapterTransitionData.number}
        mood={chapterTransitionData.mood}
        on:continue={handleChapterContinue}
      />
    {/if}

    <!-- Life Gain Animation -->
    <LifeGain show={showLifeGain} reason={lifeGainReason} />

    <!-- Bimbo Reputation Hint -->
    {#if bimboRepHint}
      <div class="bimbo-rep-hint" transition:fly={{ y: -20, duration: 400 }}>
        <span class="bimbo-rep-avatar">B</span>
        <span class="bimbo-rep-text">{bimboRepHint.hint}</span>
      </div>
    {/if}

    <!-- Ending Screen -->
    {#if showEnding}
      <EndingScreen
        {dominantCategory}
        {reputation}
        {score}
        chaptersCompleted={currentChapterIndex + 1}
        on:playAgain={handlePlayAgain}
      />
    {/if}

    <!-- Game Over Overlay -->
    {#if gameOver}
      <GameOverOverlay {score} on:restart={resetGame} />
    {/if}

    <!-- Audio Controls -->
    <div class="audio-controls">
      <button
        class="control-btn"
        class:active={autoNarrate}
        class:muted={!autoNarrate}
        on:click={toggleAutoNarrate}
        title={autoNarrate ? 'Auto-narrate ON' : 'Auto-narrate OFF'}
      >
        {#if autoNarrate}
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/></svg>
        {:else}
          <svg viewBox="0 0 24 24" fill="currentColor"><path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/></svg>
        {/if}
      </button>
      <VolumeControl />
    </div>

    <!-- Dev Tools -->
    <DevTools
      bind:this={devToolsRef}
      {currentPanel}
      {story}
      {reputation}
      {branchHistory}
      {pendingBranch}
      {isPlaying}
      {speakResult}
      {streamingManager}
      {currentChapterIndex}
      {currentPanelIndex}
      {isRecording}
      {selectedOption}
      {previewedOption}
      on:jumpToPanel={handleDevJumpToPanel}
      on:forceCategory={handleDevForceCategory}
      on:resetReputation={handleDevResetReputation}
      on:clearBranchHistory={handleDevClearBranchHistory}
      on:clearPendingBranch={handleDevClearPendingBranch}
      on:injectAudio={injectAudio}
      on:audioFileChange={handleDevAudioFileChange}
      on:infiniteLives={handleDevInfiniteLives}
    />

    <!-- Progress bar -->
    <div class="progress-bar">
      <div class="progress-fill" style="width: {progress}%"></div>
    </div>

    <!-- Chapter title -->
    {#key currentChapter?.id}
      <div class="chapter-title" in:fade={{ duration: 300 }}>
        {currentChapter?.title}
      </div>
    {/key}

    <!-- Blurred fullscreen backdrop — ambient atmosphere; the sharp hero
         image lives inside the aspect-correct .panel frame below. Decoupling
         them lets wide / square / tall panels keep their intended composition
         on any viewport without stretching. -->
    {#key currentPanel?.id}
      {#if currentPanel?.image || fallbackCharacterImage}
        <div
          class="panel-backdrop"
          style="background-image: url({currentPanel?.image || fallbackCharacterImage})"
          in:fade={{ duration: 400 }}
        ></div>
      {/if}
    {/key}

    <!-- Panel display -->
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div class="panel-container" on:click={handlePanelClick}>
      {#key currentPanel?.id}
        <div
          class="panel panel--{currentPanel?.aspect || 'square'}"
          class:panel--time-freeze={isTimeFrozen}
          in:fade={{ duration: 400 }}
        >
          <div
            class="panel-image"
            style="background: {panelBg}"
          ></div>

          {#if isTimeFrozen}
            <div class="freeze-overlay" transition:fade={{ duration: 300 }}>
              <div class="freeze-vignette"></div>
              <div class="freeze-particles">
                {#each Array(20) as _, i}
                  <div class="particle" style="--delay: {i * 0.1}s; --x: {Math.random() * 100}%; --y: {Math.random() * 100}%"></div>
                {/each}
              </div>
            </div>
          {/if}

          {#if isTimeFrozen}
            <div class="effect-badge freeze" transition:scale={{ duration: 300 }}>
              ⏸ TIME FROZEN
            </div>
          {/if}
        </div>
      {/key}
    </div>

    <!-- Time Stop Panel with options -->
    {#if isTimeFrozen && hasOptions}
      <div class="choices-section" transition:fly={{ y: 50, duration: 400 }}>
        <TimeStopPanel
          options={formattedOptions}
          {selectedOption}
          {previewedOption}
          {draftText}
          {bimboHint}
          {askingBimbo}
          lang={uiLang}
          {assistantName}
          isPreviewPlaying={isPlaying && !!previewedOption}
          on:previewOption={handleOptionPreview}
          on:playAudio={handlePlayAudio}
          on:draftChange={(e) => draftText = e.detail}
          on:askBimbo={handleAskBimbo}
          on:playBimboTranslation={handlePlayBimboTranslation}
        />

        {#if hasOptions}
          <!-- Live recording indicator — always visible while isRecording so the
               user has unambiguous feedback the mic is active and audio is being
               captured. Shows a pulsing red dot, a 'Grabando…' label, and a
               real-time mic-level bar driven by the AnalyserNode (RMS of the
               frequency-domain data). Switches to 'Procesando…' once stopped. -->

          <!-- Result feedback -->
          <SpeakResultCard
            {speakResult}
            {bimboReaction}
            {bimboReactionLoading}
            {isPlaying}
            lang={uiLang}
            on:continue={handleSpeakResultContinue}
            on:playBimboReaction={() => { if (audioEngine) audioEngine.playBimboReaction(bimboReaction); }}
          />

          <!-- Speak button -->
          <div class="speak-section">
            <SpeakButton
              {isRecording}
              isEvaluating={evaluating}
              isTimeStopped={true}
              analyser={audioAnalyser}
              lang={uiLang}
              on:toggle={toggleRecording}
            />
          </div>
        {/if}
      </div>
    {/if}

    <!-- Live mic indicator — rendered OUTSIDE the hasOptions block and
         positioned as a fixed overlay so it is ALWAYS visible when recording
         or processing, regardless of where the user has scrolled. Was
         previously nested near the mic button where it could sit off-screen
         on mobile and the user would miss it entirely. -->
    {#if isRecording || evaluating}
      <div class="mic-live mic-live-fixed" transition:fade={{ duration: 120 }}>
        <div class="mic-live-row">
          <span class="mic-live-dot" class:recording={isRecording} class:processing={!isRecording && evaluating}></span>
          <span class="mic-live-label">
            {#if isRecording}{t('recording', uiLang)}{:else}{t('processing_audio', uiLang)}{/if}
          </span>
          {#if isRecording}
            <span class="mic-live-level">
              <span class="mic-live-level-fill" style="transform: scaleX({micLevel.toFixed(3)})"></span>
            </span>
          {/if}
        </div>
        {#if liveTranscript}
          <div class="mic-live-transcript">"{liveTranscript}"</div>
        {:else if isRecording}
          <div class="mic-live-hint">{t('speak_now_hint', uiLang)}</div>
        {:else if evaluating}
          <div class="mic-live-hint">{t('sending_audio', uiLang)}</div>
        {/if}
      </div>
    {/if}

    <!-- Text box — hidden entirely during time-freeze w/ options; the overlay
         already provides all the context the learner needs, keeping the Bimbo
         narration visible underneath caused text to peek around the Speak
         button and compete for attention. -->
    {#if !(isTimeFrozen && hasOptions)}
      <TextBox
        {currentPanel}
        {isPlaying}
        minimized={false}
        on:playNarration={() => { userHasInteracted = true; if (audioEngine) audioEngine.playNarration(); }}
        on:playDialogue={() => { userHasInteracted = true; if (audioEngine) audioEngine.playDialogue(); }}
        on:stopAudio={stopAudio}
      />
    {/if}

    <!-- Navigation -->
    <div class="nav-bar">
      <button class="nav-btn" on:click={prevPanel} disabled={currentPanelNumber <= 1}>
        {t('back', narrationLanguage)}
      </button>
      <span class="panel-counter">
        {currentPanelNumber} / {totalPanels}
      </span>
      <!-- Nav primary action: hidden during time-freeze because the overlay
           already shows the Release Time & Speak action; two buttons for the
           same action was confusing. -->
      {#if !isTimeFrozen}
        <button
          class="nav-btn nav-btn--primary"
          on:click={() => {
            if (isLastPanel) handleFinishStory();
            else nextPanel();
          }}
          disabled={isPlaying}
        >
          {isLastPanel ? t('finish', narrationLanguage) : t('next', narrationLanguage)}
        </button>
      {:else}
        <span class="nav-btn-placeholder"></span>
      {/if}
    </div>
  {/if}
</div>

<style>
  .player {
    min-height: 100vh;
    min-height: 100dvh;
    background: transparent;
    color: #fff;
    display: flex;
    flex-direction: column;
    font-family: 'Segoe UI', system-ui, sans-serif;
    position: relative;
  }

  .player.time-frozen {
    background: transparent;
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100vh;
    gap: 1rem;
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 3px solid #333;
    border-top-color: #a855f7;
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .error {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100vh;
    color: #ef4444;
    font-size: 1.2rem;
  }

  .progress-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: #1f1f1f;
    z-index: 100;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #a855f7, #06b6d4);
    transition: width 0.3s ease;
  }

  .chapter-title {
    position: fixed;
    top: 12px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.875rem;
    color: #a1a1aa;
    z-index: 50;
    text-align: center;
  }

  .audio-controls {
    position: fixed;
    top: 16px;
    left: 70px;
    z-index: 100;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .control-btn {
    /* Was rgba(255,255,255,0.1) bg + 0.15 border + 0.7 text — low discoverability
       on varied panel backgrounds. Solid dark pill + brighter purple border keeps
       the audio controls visible against both bright/dark hero art. */
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(15, 15, 25, 0.75);
    border: 1px solid rgba(168, 85, 247, 0.4);
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s ease;
    padding: 0;
    color: #e9d5ff;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
  }

  .control-btn:hover {
    background: rgba(255, 255, 255, 0.2);
    color: white;
  }

  .control-btn.active {
    background: rgba(139, 92, 246, 0.3);
    border-color: rgba(139, 92, 246, 0.5);
    color: #c4b5fd;
  }

  .control-btn.muted {
    background: rgba(239, 68, 68, 0.2);
    border-color: rgba(239, 68, 68, 0.4);
    color: #fca5a5;
  }

  .control-btn svg {
    width: 18px;
    height: 18px;
  }

  .panel-container {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 3rem 1rem 1rem;
    cursor: pointer;
    min-height: 0;
    overflow: hidden;
  }

  /* Fullscreen blurred ambient backdrop — the panel's hero image enlarged,
     blurred, and dimmed to fill behind the aspect-correct frame. Takes the
     place of the old `position:fixed inset:0 cover` panel-image. */
  .panel-backdrop {
    position: fixed;
    inset: -8%;
    z-index: 0;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    filter: blur(32px) brightness(0.42) saturate(1.1);
    pointer-events: none;
    transform: translateZ(0);
  }

  .panel {
    /* Aspect-honoring frame. Width + aspect-ratio sized per panel_type;
       max-height prevents overflow when a tall panel meets a short viewport. */
    position: relative;
    margin: 0 auto;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 10px 40px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06);
    transition: box-shadow 0.5s ease;
    max-height: calc(100dvh - 220px);
    max-height: calc(100vh - 220px);
  }

  .panel--wide {
    aspect-ratio: 16 / 9;
    width: min(900px, 92vw);
  }
  .panel--square {
    aspect-ratio: 1 / 1;
    width: min(560px, 90vw);
  }
  .panel--tall {
    aspect-ratio: 9 / 16;
    width: min(380px, 72vw);
  }

  .panel--time-freeze {
    box-shadow: 0 0 60px rgba(99, 102, 241, 0.4), 0 0 0 1px rgba(168, 85, 247, 0.4);
  }

  .panel-image {
    /* Fills the aspect-correct .panel frame cleanly (image aspect matches
       frame aspect per backend's panel_type → aspect map). Was position:fixed
       inset:0 which ignored the frame entirely and stretched the image to
       the whole viewport. */
    position: absolute;
    inset: 0;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    pointer-events: none;
  }

  /* Narrow viewports: let tall panels take more width, trim container padding. */
  @media (max-width: 640px) {
    .panel--wide { width: 94vw; }
    .panel--square { width: 90vw; }
    .panel--tall { width: 82vw; max-height: 65dvh; }
  }

  .freeze-overlay {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }

  .freeze-vignette {
    position: absolute;
    inset: 0;
    box-shadow: inset 0 0 100px rgba(99, 102, 241, 0.3);
  }

  .freeze-particles {
    position: absolute;
    inset: 0;
    overflow: hidden;
  }

  .particle {
    position: absolute;
    width: 4px;
    height: 4px;
    background: rgba(167, 139, 250, 0.6);
    border-radius: 50%;
    left: var(--x);
    top: var(--y);
    animation: float 3s ease-in-out infinite;
    animation-delay: var(--delay);
  }

  @keyframes float {
    0%, 100% { transform: translateY(0) scale(1); opacity: 0.6; }
    50% { transform: translateY(-20px) scale(1.2); opacity: 1; }
  }

  .effect-badge {
    position: absolute;
    top: 1rem;
    left: 50%;
    transform: translateX(-50%);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.1em;
  }

  .effect-badge.freeze {
    background: rgba(99, 102, 241, 0.9);
    color: white;
    animation: pulse-badge 2s ease-in-out infinite;
  }

  @keyframes pulse-badge {
    0%, 100% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.5); }
    50% { box-shadow: 0 0 40px rgba(99, 102, 241, 0.8); }
  }

  .choices-section {
    /* Was in-flow (appended after panel-container → pushed layout past 100vh,
       Release Time button at rect.top:999 on 768px laptops). Now an overlay
       anchored above the nav-bar, with its own internal scroll. The sticky
       speak-section inside it keeps the Release button at the bottom edge
       even when choice cards exceed overlay height. */
    position: fixed;
    left: 0;
    right: 0;
    bottom: 72px;  /* above nav-bar */
    z-index: 150;
    padding: 0 1rem;
    max-height: calc(100vh - 160px);
    max-height: calc(100dvh - 160px);
    overflow-y: auto;
    scrollbar-width: thin;
    display: flex;
    flex-direction: column;
    align-items: center;
    pointer-events: none;  /* let clicks pass through gaps */
  }
  .choices-section > :global(*) {
    pointer-events: auto;  /* re-enable on actual children */
    width: 100%;
    max-width: 640px;
  }

  .live-transcript {
    margin-top: 0.75rem;
    padding: 0.5rem 1rem;
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 8px;
    color: #c4b5fd;
    font-size: 1.1rem;
    text-align: center;
    font-style: italic;
    max-width: 520px;
    margin-left: auto;
    margin-right: auto;
  }

  /* Live mic indicator — unmissable feedback while recording or processing */
  .mic-live {
    margin: 0.75rem auto;
    padding: 0.75rem 1rem;
    background: rgba(239, 68, 68, 0.95);
    border: 2px solid rgba(239, 68, 68, 0.9);
    border-radius: 14px;
    max-width: 520px;
    color: #fff;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.55);
  }
  /* Fixed-position variant — anchored to the top of the viewport so the user
     cannot miss it, even if the panel is scrolled or the suggestions take up
     the whole screen on mobile. */
  .mic-live.mic-live-fixed {
    position: fixed;
    left: 50%;
    transform: translateX(-50%);
    top: calc(env(safe-area-inset-top, 0px) + 72px);
    width: calc(100% - 32px);
    max-width: 420px;
    z-index: 9999;
  }
  .mic-live-row {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .mic-live-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #94a3b8;
    flex-shrink: 0;
  }
  .mic-live-dot.recording {
    background: #ef4444;
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6);
    animation: pulse-dot 1.3s ease-out infinite;
  }
  .mic-live-dot.processing {
    background: #a78bfa;
    animation: spin-pulse 1.1s linear infinite;
  }
  .mic-live-label {
    font-weight: 700;
    letter-spacing: 0.02em;
    font-size: 0.95rem;
    color: #fef2f2;
  }
  .mic-live-level {
    flex: 1;
    height: 10px;
    background: rgba(255, 255, 255, 0.09);
    border-radius: 5px;
    overflow: hidden;
    margin-left: 6px;
  }
  .mic-live-level-fill {
    display: block;
    height: 100%;
    width: 100%;
    transform-origin: left center;
    background: linear-gradient(90deg, #fca5a5, #ef4444, #fbbf24);
    transition: transform 90ms linear;
    will-change: transform;
  }
  .mic-live-transcript {
    margin-top: 8px;
    font-style: italic;
    font-size: 1.05rem;
    color: #fff1f2;
  }
  .mic-live-hint {
    margin-top: 6px;
    font-size: 0.85rem;
    color: #fecaca;
    opacity: 0.85;
  }
  /* Numeric debug readout of raw RMS * 100 so you can confirm the mic is
     actually reaching the analyser (0 = silence, 20+ = speaking). */
  .mic-live-debug {
    margin-top: 4px;
    font-size: 0.75rem;
    color: #fff;
    opacity: 0.65;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  @keyframes pulse-dot {
    0%   { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }
    80%  { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);  }
    100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);     }
  }
  @keyframes spin-pulse {
    0%   { opacity: 0.6; transform: scale(1); }
    50%  { opacity: 1;   transform: scale(1.12); }
    100% { opacity: 0.6; transform: scale(1); }
  }

  .speak-section {
    /* Visually extend the TimeStopPanel's dark container — same backdrop,
       no gap, so the Release button reads as the panel's bottom-row CTA
       instead of a floating alien over the Bimbo dialogue. */
    display: flex;
    justify-content: center;
    margin: -8px auto 0;
    width: 100%;
    max-width: 560px;
    background: rgba(10, 10, 20, 0.72);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    border: 1px solid rgba(168, 85, 247, 0.25);
    border-top: none;
    border-radius: 0 0 16px 16px;
    padding: 12px 16px 14px;
  }

  .nav-btn-placeholder {
    /* Preserves nav-bar flex spacing when the primary button is hidden
       during time-freeze (so Back stays left, counter stays centered). */
    width: 100px;
  }

  .nav-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    padding-bottom: max(0.75rem, env(safe-area-inset-bottom, 0.75rem));
    /* Was #0a0a0a but it kept getting visually buried under TextBox / Bimbo
       dialogue overlay during time-freeze. Pull above with explicit z-index
       so clickable controls are never obscured, and give it a stronger
       bottom-rooted gradient so the bar always reads as the fixed anchor
       for navigation. */
    background: linear-gradient(to top, #0a0a0a 70%, rgba(10, 10, 10, 0.85));
    border-top: 1px solid rgba(168, 85, 247, 0.25);
    position: relative;
    z-index: 200;
  }

  .nav-btn {
    padding: 0.6rem 1.1rem;
    background: #27272a;
    border: 1px solid #52525b;
    border-radius: 8px;
    color: #e4e4e7;
    font-size: 0.9rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .nav-btn:hover:not(:disabled) {
    background: #3f3f46;
    border-color: #71717a;
    color: #fff;
  }

  .nav-btn:disabled {
    opacity: 0.35;
    cursor: not-allowed;
  }

  .nav-btn--primary {
    /* Was flat #6366f1 which was hard to distinguish from the nav-bar
       background when the bar itself got partially covered. Bright gradient
       pill with box-shadow is unmistakable regardless of overlay z-order. */
    background: linear-gradient(135deg, #a78bfa, #6366f1);
    border: 1px solid rgba(168, 85, 247, 0.6);
    color: white;
    font-weight: 700;
    padding: 0.65rem 1.6rem;
    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.5);
  }

  .nav-btn--primary:hover:not(:disabled) {
    background: linear-gradient(135deg, #c4b5fd, #818cf8);
    box-shadow: 0 6px 24px rgba(139, 92, 246, 0.7);
    transform: translateY(-1px);
  }

  .panel-counter {
    font-size: 0.85rem;
    color: #71717a;
    font-weight: 600;
  }

  .bimbo-rep-hint {
    position: fixed;
    top: 60px;
    right: 16px;
    max-width: 280px;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.6rem 0.8rem;
    background: rgba(168, 85, 247, 0.15);
    border: 1px solid rgba(168, 85, 247, 0.3);
    border-radius: 12px;
    z-index: 150;
  }

  .bimbo-rep-avatar {
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(168, 85, 247, 0.4);
    border-radius: 50%;
    font-size: 0.7rem;
    font-weight: 700;
    color: white;
  }

  .bimbo-rep-text {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.8rem;
    font-style: italic;
    line-height: 1.4;
  }

  @media (max-width: 640px) {
    .audio-controls {
      left: 56px;
      gap: 6px;
    }

    .panel-container {
      padding: 2.5rem 0.5rem 0.5rem;
      max-height: 40vh;
    }

    .bimbo-rep-hint {
      max-width: 220px;
      right: 8px;
    }
  }
</style>
