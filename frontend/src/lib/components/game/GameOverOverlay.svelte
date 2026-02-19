<script>
  import { createEventDispatcher } from 'svelte';
  import { fade, scale } from 'svelte/transition';

  const dispatch = createEventDispatcher();

  export let score = 0;
</script>

<div class="game-over-overlay" transition:fade={{ duration: 500 }}>
  <div class="game-over-content" in:scale={{ duration: 400, delay: 200 }}>
    <h1 class="game-over-title">Time Anchor Destabilized</h1>
    <p class="game-over-subtitle">The simulation has collapsed. Your words weren't enough to hold reality together.</p>
    <div class="game-over-score">Final Score: {score}</div>
    <button class="game-over-btn" on:click={() => dispatch('restart')}>
      Rewind to Beginning
    </button>
  </div>
</div>

<style>
  .game-over-overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: rgba(0, 0, 0, 0.92);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .game-over-content {
    text-align: center;
    padding: 2rem;
    max-width: 480px;
  }

  .game-over-title {
    font-size: 2rem;
    font-weight: 800;
    color: #ef4444;
    margin: 0 0 1rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    text-shadow: 0 0 40px rgba(239, 68, 68, 0.5);
  }

  .game-over-subtitle {
    font-size: 1rem;
    color: #a1a1aa;
    line-height: 1.6;
    margin: 0 0 2rem;
  }

  .game-over-score {
    font-size: 1.25rem;
    font-weight: 600;
    color: #c4b5fd;
    margin-bottom: 2rem;
  }

  .game-over-btn {
    padding: 0.75rem 2rem;
    background: #6366f1;
    border: none;
    border-radius: 8px;
    color: white;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
  }

  .game-over-btn:hover {
    background: #4f46e5;
  }

  @media (max-width: 640px) {
    .game-over-title { font-size: 1.5rem; }
  }
</style>
