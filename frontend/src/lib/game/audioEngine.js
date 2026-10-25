// Audio engine — factory module for TTS playback

import { getTTS } from '$lib/api';
import { masterVolume, playbackSpeed } from '$lib/audioStore';

const TTS_PROVIDER = 'elevenlabs';

function getVoiceForSpeaker(speaker) {
  return {
    provider: TTS_PROVIDER,
    character: speaker,
    role: speaker === 'bimbo' ? 'bimbo' : 'npc',
  };
}

function getNarratorVoice() {
  return {
    provider: TTS_PROVIDER,
    character: 'narrator',
    role: 'narrator',
  };
}

function splitByLanguage(text) {
  // Split text into segments of Japanese vs non-Japanese (English).
  const segments = [];
  let current = '';
  let currentIsJa = null;
  for (const ch of text) {
    const code = ch.codePointAt(0);
    const isJa = (code >= 0x3040 && code <= 0x309F) ||  // Hiragana
                 (code >= 0x30A0 && code <= 0x30FF) ||  // Katakana
                 (code >= 0x4E00 && code <= 0x9FFF) ||  // CJK
                 (code >= 0x3000 && code <= 0x303F);    // CJK punctuation
    if (currentIsJa !== null && isJa !== currentIsJa && current.trim()) {
      segments.push({ text: current.trim(), lang: currentIsJa ? 'ja' : 'en' });
      current = '';
    }
    current += ch;
    if (!(/\s/.test(ch))) currentIsJa = isJa;
  }
  if (current.trim()) {
    segments.push({ text: current.trim(), lang: currentIsJa ? 'ja' : 'en' });
  }
  return segments;
}

/**
 * @param {Object} opts
 * @param {() => object|null} opts.getPanel - returns current panel
 * @param {(playing: boolean) => void} opts.onPlayingChange - called when isPlaying changes
 */
export function createAudioEngine({ getPanel, onPlayingChange }) {
  let currentAudio = null;
  let audioQueue = [];
  let isProcessingQueue = false;
  let audioSessionId = 0;
  let activeSubscriptions = [];
  let _isPlaying = false;

  function setPlaying(v) {
    _isPlaying = v;
    onPlayingChange(v);
  }

  function stopAudio() {
    audioSessionId++;
    if (currentAudio) {
      currentAudio.pause();
      currentAudio.src = '';
      currentAudio = null;
    }
    activeSubscriptions.forEach(unsub => unsub());
    activeSubscriptions = [];
    audioQueue = [];
    isProcessingQueue = false;
    setPlaying(false);
  }

  async function playAudioWithSettings(url, sessionId) {
    if (sessionId !== audioSessionId) return;

    const audio = new Audio(url);
    let currentVol, currentSpeed;
    const unsubVol = masterVolume.subscribe(v => { currentVol = v; audio.volume = v; });
    const unsubSpeed = playbackSpeed.subscribe(s => { currentSpeed = s; audio.playbackRate = s; });
    activeSubscriptions.push(unsubVol, unsubSpeed);

    currentAudio = audio;

    return new Promise((resolve, reject) => {
      const cleanup = () => {
        activeSubscriptions = activeSubscriptions.filter(s => s !== unsubVol && s !== unsubSpeed);
        unsubVol();
        unsubSpeed();
        if (currentAudio === audio) currentAudio = null;
      };

      audio.onended = () => { cleanup(); resolve(undefined); };
      audio.onerror = (e) => { cleanup(); reject(e); };

      if (sessionId !== audioSessionId) {
        cleanup();
        resolve(undefined);
        return;
      }

      audio.play().catch(err => { cleanup(); reject(err); });
    });
  }

  async function processAudioQueue() {
    if (isProcessingQueue || audioQueue.length === 0) return;

    const sessionId = audioSessionId;
    isProcessingQueue = true;
    setPlaying(true);

    console.log('[Audio] Processing queue:', audioQueue.length, 'items');

    while (audioQueue.length > 0) {
      if (sessionId !== audioSessionId) break;

      const item = audioQueue.shift();
      console.log('[Audio] Playing item:', item);
      try {
        const response = await getTTS(item);
        console.log('[Audio] TTS response:', response);
        if (sessionId !== audioSessionId) break;
        if (response.skip) {
          console.log('[Audio] Skipped (no voice for character)');
          continue;
        }
        if (response.error) {
          console.error('[Audio] TTS error:', response.error);
          continue;
        }
        await playAudioWithSettings(response.url, sessionId);
      } catch (e) {
        // `e` is typically a MediaError Event thrown when the <audio> element
        // errors during preload — benign because the next queue item plays
        // normally. console.error on an Event prints the uninformative word
        // "Event" and gives the appearance of broken audio to anyone reading
        // the console. Demoted to warn with the event target src for context.
        const src = e?.target?.src || e?.target?.currentSrc || 'unknown-src';
        console.warn('[TTS] queue item playback interrupted (preload race, non-fatal):', src.slice(0, 80));
      }
    }

    if (sessionId === audioSessionId) {
      isProcessingQueue = false;
      setPlaying(false);
    }
  }

  async function autoPlayPanel(userHasInteracted) {
    const panel = getPanel();
    console.log('[Audio] autoPlayPanel called', { panel: panel?.id, userHasInteracted });
    if (!panel || !userHasInteracted) {
      console.log('[Audio] Skipping - no panel or no interaction yet');
      return;
    }

    stopAudio();

    if (panel.narration) {
      console.log('[Audio] Queuing narration');
      audioQueue.push({ text: panel.narration, ...getNarratorVoice() });
    }

    if (panel.dialogue && panel.speaker && panel.speaker !== 'player') {
      console.log('[Audio] Queuing dialogue for:', panel.speaker);
      audioQueue.push({ text: panel.dialogue, ...getVoiceForSpeaker(panel.speaker) });
    }

    if (audioQueue.length > 0) {
      console.log('[Audio] Starting queue processing');
      processAudioQueue();
    } else {
      console.log('[Audio] Nothing to play');
    }
  }

  async function playNarration() {
    const panel = getPanel();
    if (!panel?.narration || _isPlaying) return;

    stopAudio();
    const sessionId = audioSessionId;
    setPlaying(true);

    try {
      const response = await getTTS({
        text: panel.narration,
        ...getNarratorVoice(),
      });

      if (sessionId !== audioSessionId) return;
      if (response.error) throw new Error(response.error);

      await playAudioWithSettings(response.url, sessionId);
    } catch (e) {
      console.error('[TTS] Error:', e);
    } finally {
      if (sessionId === audioSessionId) setPlaying(false);
    }
  }

  async function playDialogue() {
    const panel = getPanel();
    if (!panel?.dialogue || !panel?.speaker || _isPlaying) return;

    stopAudio();
    const sessionId = audioSessionId;
    setPlaying(true);

    try {
      const response = await getTTS({
        text: panel.dialogue,
        ...getVoiceForSpeaker(panel.speaker),
      });

      if (sessionId !== audioSessionId) return;
      if (response.skip) return;
      if (response.error) throw new Error(response.error);

      await playAudioWithSettings(response.url, sessionId);
    } catch (e) {
      console.error('[TTS] Error:', e);
    } finally {
      if (sessionId === audioSessionId) setPlaying(false);
    }
  }

  async function playExample(example) {
    if (!example?.target || _isPlaying) return;

    stopAudio();
    const sessionId = audioSessionId;
    setPlaying(true);

    try {
      const response = await getTTS({
        text: example.target,
        ...getVoiceForSpeaker('bimbo'),
        language: 'ja',
        sentiment: 'encouraging'
      });

      if (sessionId !== audioSessionId) return;
      if (response.error) throw new Error(response.error);

      await playAudioWithSettings(response.url, sessionId);
    } catch (e) {
      console.error('[TTS] Error:', e);
    } finally {
      if (sessionId === audioSessionId) setPlaying(false);
    }
  }

  async function playBimboReaction(bimboReaction) {
    if (!bimboReaction?.bimboDialogue || _isPlaying) return;
    stopAudio();
    const sessionId = audioSessionId;
    setPlaying(true);
    try {
      const segments = splitByLanguage(bimboReaction.bimboDialogue);
      for (const seg of segments) {
        if (sessionId !== audioSessionId) return;
        const response = await getTTS({
          text: seg.text,
          ...getVoiceForSpeaker('bimbo'),
          ...(seg.lang === 'ja' ? { language: 'ja' } : {}),
        });
        if (sessionId !== audioSessionId) return;
        if (response.error) { console.error('[TTS] Segment error:', response.error); continue; }
        await playAudioWithSettings(response.url, sessionId);
      }
    } catch (e) {
      console.error('[TTS] Bimbo reaction error:', e);
    } finally {
      if (sessionId === audioSessionId) setPlaying(false);
    }
  }

  function destroy() {
    stopAudio();
  }

  return {
    get isPlaying() { return _isPlaying; },
    stopAudio,
    autoPlayPanel,
    playNarration,
    playDialogue,
    playExample,
    playBimboReaction,
    getVoiceForSpeaker,
    destroy,
  };
}
