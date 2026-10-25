<script>
  import { createEventDispatcher } from 'svelte';
  import { fade } from 'svelte/transition';
  import { t } from '$lib/game/i18n';

  const dispatch = createEventDispatcher();

  export let speakResult = null;
  export let bimboReaction = null;
  export let bimboReactionLoading = false;
  export let isPlaying = false;
  export let lang = '';
</script>

{#if speakResult}
  <div
    class="speak-result"
    data-testid="speak-result"
    data-tier={speakResult.tier || (speakResult.success ? 'success' : 'fail')}
    class:success={speakResult.success}
    class:tier-passable={speakResult.tier === 'passable'}
    class:tier-fumble={speakResult.tier === 'fumble'}
    class:tier-fail={speakResult.tier === 'fail'}
    transition:fade={{ duration: 150 }}
  >
    {#if speakResult.success}
      <div class="result-success-msg">{speakResult.message}</div>
    {/if}

    {#if speakResult.heard}
      <div class="result-heard">
        <span class="result-label">{t('you_said', lang)}</span> "{speakResult.heard}"
        {#if speakResult.heardPronunciation}
          <span class="result-pronunciation">[{speakResult.heardPronunciation}]</span>
        {/if}
        {#if speakResult.heardTranslation}
          <span class="result-dim">— {speakResult.heardTranslation}</span>
        {/if}
      </div>
    {/if}

    {#if speakResult.category}
      <div class="result-category" style="color: {speakResult.category.color}; border-color: {speakResult.category.color}40; background: {speakResult.category.color}15">
        {speakResult.category.icon} {speakResult.category.label}
      </div>
    {/if}

    <!-- Bimbo reaction (shared between success and fail) -->
    {#if bimboReactionLoading}
      <div class="bimbo-reaction" transition:fade={{ duration: 200 }}>
        <span class="bimbo-reaction-label">{t('bimbo_label', lang)}</span>
        <span class="bimbo-reaction-shimmer"></span>
      </div>
    {:else if bimboReaction?.bimboDialogue}
      <div class="bimbo-reaction" transition:fade={{ duration: 200 }}>
        <button class="bimbo-reaction-label speaker-btn" on:click|stopPropagation={() => dispatch('playBimboReaction')}>
          {t('bimbo_label', lang)} <span class="audio-hint">{isPlaying ? '⏸' : '🔊'}</span>
        </button>
        <span>{bimboReaction.bimboDialogue}</span>
        {#if bimboReaction.teachingNote}
          <div class="bimbo-teaching-note">{bimboReaction.teachingNote}</div>
        {/if}
      </div>
    {/if}

    {#if speakResult.success}
      <button class="continue-btn" on:click|stopPropagation={() => dispatch('continue')}>
        {t('continue', lang)}
      </button>
    {:else if speakResult.canSkip}
      <button class="skip-btn" on:click|stopPropagation={() => dispatch('continue')}>
        {t('skip', lang)}
      </button>
    {/if}
  </div>
{/if}

<style>
  .speak-result {
    margin: 0.5rem auto 0;
    text-align: center;
    max-width: 340px;
  }

  .speak-result.success {
    color: #86efac;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .result-heard {
    font-size: 0.7rem;
    color: #71717a;
    margin-bottom: 0.4rem;
  }

  .result-pronunciation {
    color: #a78bfa;
    font-style: italic;
    margin-left: 0.25em;
  }

  .result-label {
    color: #52525b;
  }

  .result-dim {
    color: #52525b;
    font-style: italic;
  }

  .result-success-msg {
    font-size: 1.1rem;
    font-weight: 700;
    color: #86efac;
    margin-bottom: 0.3rem;
  }

  .result-category {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border: 1px solid;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 0.3rem 0;
  }

  /* Tier-specific result styles */
  .speak-result.tier-passable {
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.25);
    background: rgba(251, 191, 36, 0.08);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
  }

  .speak-result.tier-fumble {
    border: 1px solid rgba(251, 146, 60, 0.25);
    background: rgba(251, 146, 60, 0.08);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
  }

  .speak-result.tier-fail {
    border: 1px solid rgba(239, 68, 68, 0.2);
    background: rgba(239, 68, 68, 0.06);
    border-radius: 8px;
    padding: 0.5rem 0.75rem;
  }

  .continue-btn {
    margin-top: 0.5rem;
    padding: 0.4rem 1.5rem;
    background: rgba(99, 102, 241, 0.3);
    border: 1px solid rgba(99, 102, 241, 0.5);
    border-radius: 8px;
    color: #c4b5fd;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }

  .continue-btn:hover {
    background: rgba(99, 102, 241, 0.5);
    border-color: rgba(99, 102, 241, 0.7);
    color: #fff;
  }

  .skip-btn {
    margin-top: 0.5rem;
    padding: 0.3rem 1rem;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 6px;
    color: #a1a1aa;
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s;
  }

  .skip-btn:hover {
    background: rgba(255, 255, 255, 0.15);
    color: #fff;
  }

  /* Bimbo reaction card */
  .bimbo-reaction {
    margin: 0.5rem 0;
    padding: 0.5rem 0.75rem;
    background: rgba(168, 85, 247, 0.1);
    border: 1px solid rgba(168, 85, 247, 0.25);
    border-radius: 8px;
    font-size: 0.78rem;
    color: #e2e0f0;
    text-align: left;
    line-height: 1.45;
  }

  .bimbo-reaction-label {
    font-weight: 700;
    color: #c084fc;
    margin-right: 0.3em;
  }

  .bimbo-reaction-label.speaker-btn {
    color: #c084fc;
    font-size: inherit;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    background: none;
    border: none;
    padding: 0;
    font-family: inherit;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .bimbo-reaction-label.speaker-btn:hover {
    opacity: 0.8;
  }

  .audio-hint {
    font-size: 0.75em;
    opacity: 0.4;
    margin-left: 0.5rem;
    font-style: normal;
    transition: opacity 0.2s;
  }

  .bimbo-reaction-label.speaker-btn:hover .audio-hint {
    opacity: 0.8;
  }

  .bimbo-teaching-note {
    margin-top: 0.35rem;
    font-size: 0.7rem;
    font-style: italic;
    color: #a78bfa;
    opacity: 0.85;
  }

  .bimbo-reaction-shimmer {
    display: inline-block;
    width: 60%;
    height: 0.75em;
    background: linear-gradient(90deg, rgba(168, 85, 247, 0.15) 25%, rgba(168, 85, 247, 0.3) 50%, rgba(168, 85, 247, 0.15) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
    vertical-align: middle;
  }

  @keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
</style>
