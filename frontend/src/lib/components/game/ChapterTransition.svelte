<script>
  import { fade, scale } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';

  export let chapterTitle = '';
  export let chapterNumber = 0;
  export let mood = 'tense';

  const dispatch = createEventDispatcher();

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
  };

  $: gradient = MOOD_GRADIENTS[mood] || MOOD_GRADIENTS.tense;

  let autoTimer;
  import { onMount, onDestroy } from 'svelte';

  onMount(() => {
    autoTimer = setTimeout(() => dispatch('continue'), 4000);
  });

  onDestroy(() => {
    if (autoTimer) clearTimeout(autoTimer);
  });
</script>

<div class="chapter-transition" style="background: {gradient}" transition:fade={{ duration: 600 }}>
  <div class="content" in:scale={{ duration: 800, delay: 200, start: 0.8 }}>
    <div class="chapter-number">Chapter {chapterNumber}</div>
    <div class="chapter-name">{chapterTitle}</div>
    <div class="divider"></div>
    <button class="continue-btn" on:click={() => dispatch('continue')}>
      Continue
    </button>
  </div>
</div>

<style>
  .chapter-transition {
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 250;
  }

  .content {
    text-align: center;
    padding: 2rem;
  }

  .chapter-number {
    font-size: 0.9rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.5);
    margin-bottom: 0.5rem;
  }

  .chapter-name {
    font-size: 2rem;
    font-weight: 300;
    color: rgba(255, 255, 255, 0.9);
    letter-spacing: 0.05em;
  }

  .divider {
    width: 60px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(168, 85, 247, 0.6), transparent);
    margin: 1.5rem auto;
  }

  .continue-btn {
    padding: 0.5rem 2rem;
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 20px;
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .continue-btn:hover {
    background: rgba(255, 255, 255, 0.2);
    color: white;
  }

  @media (max-width: 640px) {
    .chapter-name {
      font-size: 1.5rem;
    }
  }
</style>
