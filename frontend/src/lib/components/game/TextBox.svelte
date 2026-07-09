<script>
  import { createEventDispatcher, onDestroy } from 'svelte';
  import { fly, fade } from 'svelte/transition';

  const dispatch = createEventDispatcher();

  export let currentPanel = null;
  export let isPlaying = false;
  export let minimized = false;

  // Typewriter state
  let displayedNarration = '';
  let displayedDialogue = '';
  let isTyping = false;
  let typeInterval = null;
  let lastPanelId = null;
  let typeGeneration = 0; // cancellation token for stale typing sessions

  onDestroy(() => { clearInterval(typeInterval); });

  function getSpeakerName(speaker) {
    const names = {
      bimbo: 'Bimbo', hana: 'Hana', samurai: 'Samurai', player: 'You',
      wukong: 'Sun Wukong', sanzang: 'Sanzang', bajie: 'Zhu Bajie',
      wujing: 'Sha Wujing', innkeeper: 'Innkeeper', bandit_chief: 'Bandit Chief',
      jade_spirit: 'Jade Spirit', magistrate: 'Magistrate Wang',
      tea_master: 'Master Lü', narrator: 'Narrator',
    };
    return names[speaker] || speaker;
  }

  function getSpeakerColor(speaker) {
    const colors = {
      bimbo: '#a855f7', hana: '#78716c', samurai: '#dc2626', player: '#10b981',
      wukong: '#f59e0b', sanzang: '#fbbf24', bajie: '#fb923c',
      wujing: '#38bdf8', innkeeper: '#a3a3a3', bandit_chief: '#ef4444',
      jade_spirit: '#34d399', magistrate: '#818cf8', tea_master: '#94a3b8',
    };
    return colors[speaker] || '#fff';
  }

  function getSpeakerIcon(speaker) {
    const icons = {
      bimbo: '◈', wukong: '🐵', sanzang: '📿', bajie: '🐷',
      wujing: '🌊', jade_spirit: '✦', tea_master: '🍵',
      player: '▸', samurai: '⚔', hana: '❀',
    };
    return icons[speaker] || '●';
  }

  // Typewriter effect
  function typeText(fullText, setter, speed = 25) {
    const gen = typeGeneration; // capture current generation
    return new Promise((resolve) => {
      if (!fullText) { setter(''); resolve(); return; }
      let i = 0;
      isTyping = true;
      setter('');
      clearInterval(typeInterval);
      typeInterval = setInterval(() => {
        if (gen !== typeGeneration) { clearInterval(typeInterval); resolve(); return; }
        if (i < fullText.length) {
          const chunk = Math.min(3, fullText.length - i);
          setter(fullText.slice(0, i + chunk));
          i += chunk;
        } else {
          clearInterval(typeInterval);
          isTyping = false;
          resolve();
        }
      }, speed);
    });
  }

  // Skip to full text
  function skipTyping() {
    clearInterval(typeInterval);
    isTyping = false;
    if (currentPanel?.narration) displayedNarration = currentPanel.narration;
    if (currentPanel?.dialogue) displayedDialogue = currentPanel.dialogue;
  }

  // React to panel changes — only fire when ID actually changes
  $: if (currentPanel?.id && currentPanel.id !== lastPanelId) {
    lastPanelId = currentPanel.id;
    typeGeneration++; // cancel any in-flight typing
    clearInterval(typeInterval);
    const panel = currentPanel;
    displayedNarration = '';
    displayedDialogue = '';
    isTyping = false;
    // Start typewriter
    (async () => {
      if (panel.narration) {
        await typeText(panel.narration, (t) => { displayedNarration = t; }, 20);
      }
      if (panel.dialogue) {
        await typeText(panel.dialogue, (t) => { displayedDialogue = t; }, 20);
      }
    })();
  }
</script>

<!-- svelte-ignore a11y-click-events-have-key-events -->
<!-- svelte-ignore a11y-no-static-element-interactions -->
<div class="text-box" class:minimized on:click={() => isTyping && skipTyping()}>
  {#key currentPanel?.id}
    <div class="text-content" in:fly={{ y: 20, duration: 300 }}>
      {#if currentPanel?.narration}
        <p class="narration clickable" role="button" tabindex="0"
           on:click|stopPropagation={() => { skipTyping(); dispatch('playNarration'); }}
           on:keydown|stopPropagation={(e) => { if (e.key === 'Enter' || e.key === ' ') dispatch('playNarration'); }}>
          {displayedNarration}{#if isTyping && !displayedDialogue}<span class="cursor">▌</span>{/if}
          {#if !isTyping}<span class="audio-hint">🔊</span>{/if}
        </p>
      {/if}
      {#if currentPanel?.dialogue && displayedDialogue}
        <p class="dialogue" in:fly={{ y: 10, duration: 200 }}>
          {#if currentPanel?.speaker}
            {#if currentPanel.speaker === 'player'}
              <span class="speaker-tag player-tag">
                <span class="speaker-icon">{getSpeakerIcon(currentPanel.speaker)}</span>
                <span class="speaker-name" style="color: {getSpeakerColor(currentPanel.speaker)}">
                  {getSpeakerName(currentPanel.speaker)}
                </span>
              </span>
            {:else}
              <button
                class="speaker-tag"
                on:click|stopPropagation={() => { skipTyping(); dispatch('playDialogue'); }}
              >
                <span class="speaker-icon">{getSpeakerIcon(currentPanel.speaker)}</span>
                <span class="speaker-name" style="color: {getSpeakerColor(currentPanel.speaker)}">
                  {getSpeakerName(currentPanel.speaker)}
                </span>
                <span class="audio-hint">🔊</span>
              </button>
            {/if}
          {/if}
          <span class="dialogue-text">"{displayedDialogue}{#if isTyping}<span class="cursor">▌</span>{:else}"{/if}</span>
        </p>
      {/if}
    </div>
  {/key}

  {#if isTyping}
    <div class="typing-indicator">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>
  {/if}

  {#if isPlaying}
    <div class="playing-bar" transition:fade={{ duration: 200 }}>
      <div class="sound-wave">
        <span class="wave-bar"></span>
        <span class="wave-bar"></span>
        <span class="wave-bar"></span>
        <span class="wave-bar"></span>
        <span class="wave-bar"></span>
      </div>
      <span>Narrating...</span>
      <button class="stop-btn" on:click|stopPropagation={() => dispatch('stopAudio')}>Stop</button>
    </div>
  {/if}
</div>

<style>
  .text-box {
    background: linear-gradient(to top, rgba(0,0,0,0.95), rgba(0,0,0,0.8));
    padding: 1rem 1.25rem;
    min-height: 80px;
    transition: min-height 0.3s ease, opacity 0.3s ease;
  }

  .text-box.minimized {
    min-height: 60px;
    opacity: 0.7;
  }

  .text-content {
    max-width: 700px;
    margin: 0 auto;
  }

  .narration {
    font-size: 0.95rem;
    line-height: 1.7;
    color: #d4d4d8;
    margin: 0 0 0.5rem 0;
    font-style: italic;
    position: relative;
  }

  .narration.clickable {
    cursor: pointer;
    transition: color 0.2s;
  }

  .narration.clickable:hover {
    color: #fff;
  }

  .cursor {
    color: #a78bfa;
    animation: blink 0.6s step-end infinite;
    font-style: normal;
  }

  @keyframes blink {
    50% { opacity: 0; }
  }

  .audio-hint {
    font-size: 0.75em;
    opacity: 0.4;
    margin-left: 0.5rem;
    font-style: normal;
    transition: opacity 0.2s;
  }

  .narration.clickable:hover .audio-hint,
  .speaker-tag:hover .audio-hint {
    opacity: 0.8;
  }

  .dialogue {
    font-size: 1.05rem;
    line-height: 1.6;
    color: #fff;
    margin: 0;
  }

  .dialogue-text {
    display: inline;
  }

  /* Speaker tag */
  .speaker-tag {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    margin-right: 0.5rem;
    margin-bottom: 0.25rem;
    padding: 0.2rem 0.6rem 0.2rem 0.4rem;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    font-size: inherit;
    font-family: inherit;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s, border-color 0.2s;
    color: inherit;
  }

  .speaker-tag:hover {
    background: rgba(255,255,255,0.1);
    border-color: rgba(255,255,255,0.2);
  }

  .speaker-tag.player-tag {
    cursor: default;
    background: rgba(16,185,129,0.1);
    border-color: rgba(16,185,129,0.2);
  }

  .speaker-icon {
    font-size: 0.9em;
    font-style: normal;
  }

  .speaker-name {
    font-weight: 700;
  }

  /* Typing indicator */
  .typing-indicator {
    display: flex;
    gap: 4px;
    padding: 0.4rem 0;
    justify-content: center;
  }

  .typing-dot {
    width: 6px;
    height: 6px;
    background: #a78bfa;
    border-radius: 50%;
    animation: typing-bounce 1.2s ease-in-out infinite;
  }

  .typing-dot:nth-child(2) { animation-delay: 0.15s; }
  .typing-dot:nth-child(3) { animation-delay: 0.3s; }

  @keyframes typing-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-6px); opacity: 1; }
  }

  /* Playing bar with sound wave */
  .playing-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0;
    font-size: 0.85rem;
    color: #a78bfa;
  }

  .sound-wave {
    display: flex;
    align-items: flex-end;
    gap: 2px;
    height: 16px;
  }

  .wave-bar {
    width: 3px;
    background: #a78bfa;
    border-radius: 2px;
    animation: wave 1s ease-in-out infinite;
  }

  .wave-bar:nth-child(1) { height: 6px; animation-delay: 0s; }
  .wave-bar:nth-child(2) { height: 12px; animation-delay: 0.15s; }
  .wave-bar:nth-child(3) { height: 8px; animation-delay: 0.3s; }
  .wave-bar:nth-child(4) { height: 14px; animation-delay: 0.45s; }
  .wave-bar:nth-child(5) { height: 6px; animation-delay: 0.6s; }

  @keyframes wave {
    0%, 100% { transform: scaleY(0.5); }
    50% { transform: scaleY(1); }
  }

  .stop-btn {
    margin-left: auto;
    padding: 0.25rem 0.75rem;
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 4px;
    color: #fca5a5;
    font-size: 0.8rem;
    cursor: pointer;
  }

  @media (max-width: 640px) {
    .text-box {
      padding: 0.75rem;
      min-height: 70px;
    }

    .narration { font-size: 0.85rem; }
    .dialogue { font-size: 0.9rem; }
  }
</style>
