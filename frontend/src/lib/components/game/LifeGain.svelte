<script>
  import { fly, fade } from 'svelte/transition';
  import { onMount } from 'svelte';

  export let show = false;
  export let reason = 'perfect'; // 'perfect' | 'chapter'

  let visible = false;

  $: if (show) {
    visible = true;
    setTimeout(() => { visible = false; }, 2000);
  }
</script>

{#if visible}
  <div class="life-gain" transition:fly={{ y: 20, duration: 400 }}>
    <span class="heart">+1</span>
    <span class="label">
      {reason === 'perfect' ? 'Perfect!' : 'Chapter Complete!'}
    </span>
  </div>
{/if}

<style>
  .life-gain {
    position: fixed;
    top: 60px;
    left: 16px;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.4rem 0.8rem;
    background: rgba(34, 197, 94, 0.2);
    border: 1px solid rgba(34, 197, 94, 0.4);
    border-radius: 20px;
    z-index: 150;
    animation: pulse-life 0.6s ease-out;
  }

  .heart {
    color: #ef4444;
    font-size: 1.1rem;
    font-weight: 700;
  }

  .label {
    color: #86efac;
    font-size: 0.8rem;
    font-weight: 500;
  }

  @keyframes pulse-life {
    0% { transform: scale(0.8); opacity: 0; }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); opacity: 1; }
  }
</style>
