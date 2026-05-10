<script>
  import { createEventDispatcher } from 'svelte';

  const dispatch = createEventDispatcher();

  export let currentPanel = null;

  let devAudioFile = null;
  let devInjecting = false;
  let devAutoInject = false;
  let devAutoInjectDelay = 500;
  let devAutoInjectTimeout = null;

  export function checkAutoInject(devAudioFileRef) {
    if (devAutoInject && devAudioFileRef) {
      if (devAutoInjectTimeout) clearTimeout(devAutoInjectTimeout);
      devAutoInjectTimeout = setTimeout(() => {
        dispatch('injectAudio');
        devAutoInjectTimeout = null;
      }, devAutoInjectDelay);
    }
  }

  export function cleanup() {
    if (devAutoInjectTimeout) clearTimeout(devAutoInjectTimeout);
  }

  export function getAudioFile() {
    return devAudioFile;
  }

  function handleDevFileSelect(e) {
    devAudioFile = e.target.files?.[0] || null;
    dispatch('audioFileChange', devAudioFile);
  }
</script>

<div class="dev-separator"></div>
<div class="dev-title">Inject Audio</div>
<input type="file" accept="audio/*" class="dev-file" on:change={handleDevFileSelect} />
{#if devAudioFile}
  <div class="dev-file-name">{devAudioFile.name}</div>
  <button class="dev-inject-btn" on:click={() => dispatch('injectAudio')} disabled={devInjecting || !currentPanel?.options?.length}>
    {devInjecting ? 'Injecting...' : 'Inject'}
  </button>
  <label class="dev-option" style="margin-top:4px">
    <input type="checkbox" bind:checked={devAutoInject} />
    <span>Auto-inject on freeze</span>
  </label>
  {#if devAutoInject}
    <div class="dev-row">
      <label class="dev-label" for="auto-inject-delay">Delay (ms)</label>
      <input id="auto-inject-delay" type="number" class="dev-input-sm" min="0" max="5000" step="100" bind:value={devAutoInjectDelay} />
    </div>
  {/if}
{/if}

<style>
  .dev-separator {
    height: 1px;
    background: rgba(255, 255, 255, 0.08);
    margin: 6px 0;
  }

  .dev-title {
    font-size: 0.6rem;
    color: #52525b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
  }

  .dev-option {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.75rem;
    color: #a1a1aa;
    cursor: pointer;
    padding: 3px 0;
  }

  .dev-option input[type="checkbox"] {
    width: 14px;
    height: 14px;
    accent-color: #6366f1;
    cursor: pointer;
  }

  .dev-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 3px 0;
  }

  .dev-label {
    font-size: 0.65rem;
    color: #71717a;
    white-space: nowrap;
  }

  .dev-input-sm {
    width: 60px;
    padding: 2px 4px;
    font-size: 0.65rem;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 4px;
    color: #d4d4d8;
    text-align: center;
  }

  .dev-file {
    font-size: 0.65rem;
    color: #71717a;
    width: 100%;
    margin-top: 2px;
  }

  .dev-file::file-selector-button {
    font-size: 0.65rem;
    padding: 2px 6px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 4px;
    color: #a1a1aa;
    cursor: pointer;
    margin-right: 4px;
  }

  .dev-file-name {
    font-size: 0.6rem;
    color: #52525b;
    margin-top: 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .dev-inject-btn {
    margin-top: 4px;
    width: 100%;
    padding: 4px 8px;
    font-size: 0.7rem;
    font-weight: 600;
    background: rgba(99, 102, 241, 0.25);
    border: 1px solid rgba(99, 102, 241, 0.4);
    border-radius: 5px;
    color: #a5b4fc;
    cursor: pointer;
    transition: background 0.15s;
  }

  .dev-inject-btn:hover:not(:disabled) {
    background: rgba(99, 102, 241, 0.4);
  }

  .dev-inject-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
</style>
