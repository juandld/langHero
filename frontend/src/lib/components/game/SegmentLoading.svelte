<script>
  import { fade } from 'svelte/transition';

  export let message = 'Preparing next scene...';
</script>

<div class="segment-loading" transition:fade={{ duration: 300 }}>
  <div class="loading-inner">
    <div class="bimbo-icon">
      <div class="pulse-ring"></div>
      <div class="glow-core"></div>
    </div>
    <p class="loading-text">{message}</p>
  </div>
</div>

<style>
  .segment-loading {
    position: fixed;
    inset: 0;
    background: rgba(10, 10, 26, 0.9);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 200;
  }

  .loading-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
  }

  .bimbo-icon {
    position: relative;
    width: 60px;
    height: 60px;
  }

  .glow-core {
    position: absolute;
    inset: 15px;
    border-radius: 50%;
    background: linear-gradient(135deg, #a855f7, #06b6d4);
    animation: core-pulse 2s ease-in-out infinite;
  }

  .pulse-ring {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    border: 2px solid rgba(168, 85, 247, 0.4);
    animation: ring-expand 2s ease-out infinite;
  }

  @keyframes core-pulse {
    0%, 100% { transform: scale(1); opacity: 0.8; }
    50% { transform: scale(1.1); opacity: 1; }
  }

  @keyframes ring-expand {
    0% { transform: scale(0.8); opacity: 0.8; }
    100% { transform: scale(1.6); opacity: 0; }
  }

  .loading-text {
    color: #c4b5fd;
    font-size: 1rem;
    font-style: italic;
    letter-spacing: 0.05em;
  }
</style>
