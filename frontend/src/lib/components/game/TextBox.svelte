<script>
  import { createEventDispatcher } from 'svelte';
  import { fly, fade } from 'svelte/transition';

  const dispatch = createEventDispatcher();

  export let currentPanel = null;
  export let isPlaying = false;
  export let minimized = false;

  function getSpeakerName(speaker) {
    const names = { bimbo: 'Bimbo', hana: 'Hana', samurai: 'Samurai', player: 'You' };
    return names[speaker] || speaker;
  }

  function getSpeakerColor(speaker) {
    const colors = { bimbo: '#a855f7', hana: '#78716c', samurai: '#dc2626', player: '#10b981' };
    return colors[speaker] || '#fff';
  }
</script>

<div class="text-box" class:minimized>
  {#key currentPanel?.id}
    <div class="text-content" in:fly={{ y: 20, duration: 300 }}>
      {#if currentPanel?.narration}
        <p class="narration clickable" role="button" tabindex="0" on:click|stopPropagation={() => dispatch('playNarration')} on:keydown|stopPropagation={(e) => { if (e.key === 'Enter' || e.key === ' ') dispatch('playNarration'); }}>
          {currentPanel.narration}
          <span class="audio-hint">🔊</span>
        </p>
      {/if}
      {#if currentPanel?.dialogue}
        <p class="dialogue">
          {#if currentPanel?.speaker}
            {#if currentPanel.speaker === 'player'}
              <span class="speaker" style="color: {getSpeakerColor(currentPanel.speaker)}">
                {getSpeakerName(currentPanel.speaker)}:
              </span>
            {:else}
              <button
                class="speaker-btn"
                style="color: {getSpeakerColor(currentPanel.speaker)}"
                on:click|stopPropagation={() => dispatch('playDialogue')}
              >
                {getSpeakerName(currentPanel.speaker)}:
                <span class="audio-hint">🔊</span>
              </button>
            {/if}
          {/if}
          "{currentPanel.dialogue}"
        </p>
      {/if}
    </div>
  {/key}

  {#if isPlaying}
    <div class="playing-bar" transition:fade={{ duration: 200 }}>
      <span class="playing-dot"></span>
      <span>Playing...</span>
      <button class="stop-btn" on:click|stopPropagation={() => dispatch('stopAudio')}>Stop</button>
    </div>
  {/if}
</div>

<style>
  .text-box {
    background: linear-gradient(to top, rgba(0,0,0,0.95), rgba(0,0,0,0.8));
    padding: 1rem;
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
    line-height: 1.6;
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

  .audio-hint {
    font-size: 0.75em;
    opacity: 0.4;
    margin-left: 0.5rem;
    font-style: normal;
    transition: opacity 0.2s;
  }

  .narration.clickable:hover .audio-hint,
  .speaker-btn:hover .audio-hint {
    opacity: 0.8;
  }

  .dialogue {
    font-size: 1rem;
    line-height: 1.6;
    color: #fff;
    margin: 0;
  }

  .speaker {
    font-weight: 600;
    margin-right: 0.5rem;
  }

  .speaker-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    font-weight: 600;
    margin-right: 0.5rem;
    background: none;
    border: none;
    padding: 0;
    font-size: inherit;
    font-family: inherit;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .speaker-btn:hover {
    opacity: 0.8;
  }

  .playing-bar {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0;
    font-size: 0.85rem;
    color: #a78bfa;
  }

  .playing-dot {
    width: 8px;
    height: 8px;
    background: #a78bfa;
    border-radius: 50%;
    animation: pulse-dot 1s ease-in-out infinite;
  }

  @keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
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
