<script>
  import { fade, scale } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';

  export let dominantCategory = 'pragmatic';
  export let reputation = {};
  export let score = 0;
  export let chaptersCompleted = 15;

  const dispatch = createEventDispatcher();

  const ENDINGS = {
    diplomatic: {
      title: 'The Ambassador',
      quote: 'Words built this bridge.',
      color: '#86efac',
      gradient: 'linear-gradient(135deg, #0a2e1a 0%, #1a3e2a 50%, #0a4e3a 100%)',
      description: 'You walked between worlds with grace. Every word a handshake, every phrase a treaty. Japan remembers the foreigner who spoke peace into being.',
    },
    pragmatic: {
      title: 'The Survivor',
      quote: 'Words kept you alive.',
      color: '#93c5fd',
      gradient: 'linear-gradient(135deg, #0a1a2e 0%, #1a2a3e 50%, #0a3a4e 100%)',
      description: 'You chose your words like tools — each one precisely placed, each one serving a purpose. You survived not by luck, but by understanding.',
    },
    bold: {
      title: 'The Legend',
      quote: 'Words made you immortal.',
      color: '#fdba74',
      gradient: 'linear-gradient(135deg, #2e1a0a 0%, #3e2a1a 50%, #4e3a0a 100%)',
      description: 'Your voice rang through castle halls and across battlefields. They still tell stories of the foreigner who spoke like thunder.',
    },
    hostile: {
      title: 'The Lone Wolf',
      quote: 'Words are weapons. You proved it.',
      color: '#fca5a5',
      gradient: 'linear-gradient(135deg, #2e0a0a 0%, #3e1a1a 50%, #4e0a0a 100%)',
      description: 'You carved your path with sharp words and sharper will. Not everyone survived your honesty. But you remained unbroken.',
    },
    'history-breaking': {
      title: 'The One Who Changed Everything',
      quote: 'Words rewrote the world.',
      color: '#e9d5ff',
      gradient: 'linear-gradient(135deg, #1a0a2e 0%, #2a1a3e 50%, #1a0a4e 100%)',
      description: 'You spoke words that shouldn\'t exist — ideas from another time woven into feudal Japanese. The simulation couldn\'t contain you. Neither could history.',
    },
  };

  $: ending = ENDINGS[dominantCategory] || ENDINGS.pragmatic;

  // Count total reputation
  $: totalReputation = Object.values(reputation).reduce((sum, v) => sum + v, 0);
</script>

<div class="ending-screen" style="background: {ending.gradient}" transition:fade={{ duration: 800 }}>
  <div class="content" in:scale={{ duration: 1000, delay: 300, start: 0.85 }}>
    <div class="ending-label">Your Ending</div>
    <h1 class="ending-title" style="color: {ending.color}">{ending.title}</h1>
    <div class="quote">"{ending.quote}"</div>
    <div class="divider"></div>
    <p class="description">{ending.description}</p>

    <div class="stats">
      <div class="stat">
        <span class="stat-value">{chaptersCompleted}</span>
        <span class="stat-label">Chapters</span>
      </div>
      <div class="stat">
        <span class="stat-value">{score}</span>
        <span class="stat-label">Score</span>
      </div>
      <div class="stat">
        <span class="stat-value">{totalReputation}</span>
        <span class="stat-label">Reputation</span>
      </div>
    </div>

    <div class="reputation-breakdown">
      {#each Object.entries(reputation) as [cat, val]}
        {#if val > 0}
          <span class="rep-tag">{cat}: {val}</span>
        {/if}
      {/each}
    </div>

    <button class="play-again" on:click={() => dispatch('playAgain')}>
      Play Again
    </button>
  </div>
</div>

<style>
  .ending-screen {
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 300;
    overflow-y: auto;
  }

  .content {
    text-align: center;
    padding: 2rem;
    max-width: 500px;
  }

  .ending-label {
    font-size: 0.8rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: rgba(255, 255, 255, 0.4);
    margin-bottom: 0.5rem;
  }

  .ending-title {
    font-size: 2.5rem;
    font-weight: 300;
    margin: 0.5rem 0;
    letter-spacing: 0.05em;
  }

  .quote {
    font-style: italic;
    color: rgba(255, 255, 255, 0.6);
    font-size: 1.1rem;
    margin-bottom: 1rem;
  }

  .divider {
    width: 80px;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    margin: 1.5rem auto;
  }

  .description {
    color: rgba(255, 255, 255, 0.7);
    line-height: 1.6;
    font-size: 0.95rem;
    margin-bottom: 2rem;
  }

  .stats {
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-bottom: 1.5rem;
  }

  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
  }

  .stat-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: rgba(255, 255, 255, 0.9);
  }

  .stat-label {
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.4);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .reputation-breakdown {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 0.5rem;
    margin-bottom: 2rem;
  }

  .rep-tag {
    padding: 0.25rem 0.75rem;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.6);
  }

  .play-again {
    padding: 0.75rem 2.5rem;
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.3);
    border-radius: 25px;
    color: white;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s ease;
  }

  .play-again:hover {
    background: rgba(255, 255, 255, 0.25);
    transform: translateY(-1px);
  }

  @media (max-width: 640px) {
    .ending-title { font-size: 1.8rem; }
    .stats { gap: 1.5rem; }
  }
</style>
