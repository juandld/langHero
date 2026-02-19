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
  import { RESPONSE_CATEGORIES, STYLE_TO_CATEGORY, getOptionCategory, getCategoryKey, resolveBranch, resolvePanel, findPanelLocation } from '$lib/game/branchLogic';
  import { fetchTtsUrl } from '$lib/utils/ttsCache';

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

  const API_BASE = getApiBase();
  const AUTO_NARRATE_KEY = 'LANGHERO_AUTO_NARRATE_V1';

  // Story state
  let story = null;
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
  $: totalPanels = story?.chapters?.reduce((sum, ch) => sum + ch.panels.length, 0) || 0;

  $: isLastPanel = currentChapterIndex === (story?.chapters?.length || 1) - 1 &&
                   currentPanelIndex === (currentChapter?.panels?.length || 1) - 1;

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

  $: progress = totalPanels > 0 ? (currentPanelNumber / totalPanels) * 100 : 0;

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
      score,
      lives,
      livesTotal,
      choices,
      reputation,
      branchHistory,
    });
  }

  function loadProgress() {
    const saved = getJson(STORAGE_KEYS.STORY_PROGRESS, null);
    if (!saved || saved.storyId !== storyId) return;
    currentChapterIndex = saved.chapterIndex ?? 0;
    currentPanelIndex = saved.panelIndex ?? 0;
    score = saved.score ?? 0;
    lives = saved.lives ?? 3;
    livesTotal = saved.livesTotal ?? 3;
    choices = saved.choices ?? {};
    reputation = saved.reputation ?? { diplomatic: 0, pragmatic: 0, bold: 0, hostile: 0, 'history-breaking': 0 };
    branchHistory = saved.branchHistory ?? [];
    if (lives <= 0) gameOver = true;
  }

  function resetGame() {
    currentChapterIndex = 0;
    currentPanelIndex = 0;
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
    stopAudio();
    cleanupRecording();
    saveProgress();
  }

  onMount(async () => {
    autoNarrate = loadAutoNarrate();

    // Create audio engine
    audioEngine = createAudioEngine({
      getPanel: () => currentPanel,
      onPlayingChange: (v) => { isPlaying = v; },
    });

    try {
      const [storyRes, voiceRes] = await Promise.all([
        fetch(`${API_BASE}/api/story-panels/stories/${storyId}`),
        fetch(`${API_BASE}/api/story-panels/stories/${storyId}/voice-config`)
      ]);

      if (!storyRes.ok) throw new Error('Story not found');
      story = await storyRes.json();

      if (voiceRes.ok) {
        voiceConfig = await voiceRes.json();
      }

      // Restore saved progress after story loads
      loadProgress();
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
      getLanguage: () => 'Japanese',
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
        speakResult = { success: false, message: data.message || 'Try in Japanese' };
        isRecording = false;
        evaluating = false;
        cleanupRecording();
      },
      onError: (err) => {
        console.error('[Speech] Error:', err);
        speakResult = { success: false, message: 'Connection error - try again' };
        isRecording = false;
        evaluating = false;
        cleanupRecording();
      },
    });
  }

  async function toggleRecording() {
    if (isRecording) {
      // Stop recording
      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        if (streamingManager) {
          streamingManager.signalStop('stop');
        }
        mediaRecorder.stop();
      }
      isRecording = false;
      evaluating = true;
      audioAnalyser = null;
      disconnectAnalyser();
    } else {
      userHasInteracted = true;
      stopAudio();
      ensureAudioContext();
      // Re-create streaming manager each time so getScenario picks up current state
      if (streamingManager) {
        streamingManager.close();
        streamingManager = null;
      }
      initStreamingManager();

      try {
        liveTranscript = '';
        speakResult = null;
        bimboReaction = null;
        bimboReactionLoading = false;

        const micId = getString(STORAGE_KEYS.MIC_DEVICE_ID, '');
        let stream;
        try {
          const audioConstraints = micId ? { deviceId: { exact: micId } } : true;
          stream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints });
        } catch (_) {
          stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }
        recordingStream = stream;
        mediaRecorder = new MediaRecorder(stream);
        audioAnalyser = setupAudioAnalyser(stream);

        mediaRecorder.ondataavailable = async (event) => {
          if (!event?.data) return;
          audioChunks.push(event.data);
          if (streamingManager) {
            await streamingManager.sendChunk(event.data);
          }
        };

        mediaRecorder.onstop = () => {
          try {
            recordingStream?.getTracks?.().forEach(t => t.stop());
          } catch (_) {}
          recordingStream = null;
          audioChunks = [];
        };

        audioChunks = [];
        streamingManager.setEnabled(true);
        streamingManager.connect();
        mediaRecorder.start(200);
        isRecording = true;

      } catch (err) {
        console.error('Error accessing microphone:', err);
        speakResult = { success: false, message: 'Microphone access denied' };
      }
    }
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
    if (recordingStream) {
      try {
        recordingStream.getTracks().forEach(t => t.stop());
      } catch (_) {}
      recordingStream = null;
    }
    if (streamingManager) {
      streamingManager.setEnabled(false);
    }
    audioAnalyser = null;
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
        currentChapterIndex++;
        currentPanelIndex = 0;
      }
    }
    saveProgress();
  }

  function prevPanel() {
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
</script>

<svelte:window on:keydown={handleKeydown} />

<GameMenu
  visible={menuVisible}
  judgeFocus={0}
  languageOverride=""
  micDevices={[]}
  micDeviceId=""
  scenariosCompleted={0}
  on:close={closeMenu}
  on:exit={handleMenuExit}
/>

<div class="player" class:time-frozen={isTimeFrozen}>
  {#if loading}
    <div class="loading">
      <div class="loading-spinner"></div>
      <p>Loading story...</p>
    </div>
  {:else if error}
    <div class="error">{error}</div>
  {:else if story}
    <!-- HUD -->
    <GameHUD {lives} {livesTotal} {score} on:openMenu={openMenu} />

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

    <!-- Panel display -->
    <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
    <div class="panel-container" on:click={handlePanelClick}>
      {#key currentPanel?.id}
        <div
          class="panel panel--{currentPanel?.aspect || 'square'}"
          class:panel--time-freeze={isTimeFrozen}
          in:fade={{ duration: 400 }}
        >
          <img
            src="{API_BASE}{currentPanel?.image}"
            alt={currentPanel?.id}
            class="panel-image"
          />

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
          isPreviewPlaying={isPlaying && !!previewedOption}
          on:previewOption={handleOptionPreview}
          on:playAudio={handlePlayAudio}
          on:draftChange={(e) => draftText = e.detail}
          on:askBimbo={handleAskBimbo}
          on:playBimboTranslation={handlePlayBimboTranslation}
        />

        {#if hasOptions}
          <!-- Live transcript -->
          {#if isRecording && liveTranscript}
            <div class="live-transcript" transition:fade={{ duration: 150 }}>
              "{liveTranscript}"
            </div>
          {/if}

          <!-- Result feedback -->
          <SpeakResultCard
            {speakResult}
            {bimboReaction}
            {bimboReactionLoading}
            {isPlaying}
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
              on:toggle={toggleRecording}
            />
          </div>
        {/if}
      </div>
    {/if}

    <!-- Text box -->
    <TextBox
      {currentPanel}
      {isPlaying}
      minimized={isTimeFrozen && hasOptions}
      on:playNarration={() => { userHasInteracted = true; if (audioEngine) audioEngine.playNarration(); }}
      on:playDialogue={() => { userHasInteracted = true; if (audioEngine) audioEngine.playDialogue(); }}
      on:stopAudio={stopAudio}
    />

    <!-- Navigation -->
    <div class="nav-bar">
      <button class="nav-btn" on:click={prevPanel} disabled={currentPanelNumber <= 1}>
        ← Back
      </button>
      <span class="panel-counter">
        {currentPanelNumber} / {totalPanels}
      </span>
      <button
        class="nav-btn nav-btn--primary"
        on:click={() => {
          if (isTimeFrozen && hasOptions) {
            toggleRecording();
          } else if (!isTimeFrozen) {
            nextPanel();
          }
        }}
        disabled={isLastPanel || isPlaying}
      >
        {#if isTimeFrozen}
          {isRecording ? 'Stop' : 'Speak'}
        {:else}
          Next →
        {/if}
      </button>
    </div>
  {/if}
</div>

<style>
  .player {
    min-height: 100vh;
    min-height: 100dvh;
    background: #0a0a0a;
    color: #fff;
    display: flex;
    flex-direction: column;
    font-family: 'Segoe UI', system-ui, sans-serif;
    transition: background 0.5s ease;
  }

  .player.time-frozen {
    background: #0a0a1a;
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
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s ease;
    padding: 0;
    color: rgba(255, 255, 255, 0.7);
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

  .panel {
    position: relative;
    max-width: 100%;
    max-height: 100%;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 10px 40px rgba(0,0,0,0.5);
    transition: box-shadow 0.5s ease;
  }

  .panel--wide { max-width: min(900px, 95vw); }
  .panel--square { max-width: min(500px, 90vw); }
  .panel--tall { max-width: min(400px, 80vw); }

  .panel--time-freeze {
    box-shadow: 0 0 60px rgba(99, 102, 241, 0.4);
  }

  .panel-image {
    display: block;
    width: 100%;
    height: auto;
    max-height: 800px;
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
    padding: 0 1rem;
    margin-bottom: 0.5rem;
    flex-shrink: 0;
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

  .speak-section {
    margin-top: 1rem;
    display: flex;
    justify-content: center;
  }

  .nav-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    padding-bottom: max(0.75rem, env(safe-area-inset-bottom, 0.75rem));
    background: #0a0a0a;
    border-top: 1px solid #1f1f1f;
  }

  .nav-btn {
    padding: 0.5rem 1rem;
    background: #27272a;
    border: 1px solid #3f3f46;
    border-radius: 8px;
    color: #a1a1aa;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .nav-btn:hover:not(:disabled) {
    background: #3f3f46;
    color: #fff;
  }

  .nav-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .nav-btn--primary {
    background: #6366f1;
    border-color: #6366f1;
    color: white;
  }

  .nav-btn--primary:hover:not(:disabled) {
    background: #4f46e5;
  }

  .panel-counter {
    font-size: 0.85rem;
    color: #71717a;
    font-weight: 600;
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
  }
</style>
