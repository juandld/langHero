<script>
  import { createEventDispatcher } from 'svelte';
  import { fly } from 'svelte/transition';

  import ForceCategory from './ForceCategory.svelte';
  import RecordClip from './RecordClip.svelte';
  import AudioInjector from './AudioInjector.svelte';
  import ResultInspector from './ResultInspector.svelte';
  import BranchInspector from './BranchInspector.svelte';
  import PanelJumpNav from './PanelJumpNav.svelte';

  const dispatch = createEventDispatcher();

  // Props — read-only game state
  export let currentPanel = null;
  export let story = null;
  export let reputation = {};
  export let branchHistory = [];
  export let pendingBranch = null;
  export const isPlaying = false;
  export const speakResult = null;
  export const streamingManager = null;
  export let currentChapterIndex = 0;
  export let currentPanelIndex = 0;
  export let isRecording = false;
  export let selectedOption = null;
  export let previewedOption = null;

  // Drawer state
  let devMenuOpen = false;
  let infiniteLives = false;

  // Child refs
  let recordClipRef;
  let audioInjectorRef;
  let resultInspectorRef;

  // Expose for parent
  export function getInfiniteLives() { return infiniteLives; }
  export function getDevLastResult() { return resultInspectorRef?.getDevLastResult?.(); }
  export function setDevLastResult(r) { resultInspectorRef?.setDevLastResult(r); }
  export function setDevLastLang(l) { resultInspectorRef?.setDevLastLang(l); }
  export function checkAutoInject(devAudioFileRef) { audioInjectorRef?.checkAutoInject(devAudioFileRef); }

  export function cleanup() {
    recordClipRef?.cleanup();
    audioInjectorRef?.cleanup();
  }

  $: dispatch('infiniteLives', infiniteLives);
</script>

{#if import.meta.env.DEV}
  <div class="dev-tools">
    <button class="dev-btn" on:click={() => devMenuOpen = !devMenuOpen} title="Dev tools" aria-label="Dev tools">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
      </svg>
    </button>
    {#if devMenuOpen}
      <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
      <div class="dev-overlay" on:click={() => devMenuOpen = false}></div>
      <div class="dev-drawer" transition:fly={{ x: 320, duration: 200 }}>
        <div class="dev-title">Dev Tools</div>
        <label class="dev-option">
          <input type="checkbox" bind:checked={infiniteLives} />
          <span>Infinite lives</span>
        </label>

        <ForceCategory {currentPanel} on:forceCategory />

        <RecordClip
          bind:this={recordClipRef}
          {isRecording}
          {currentPanel}
          {selectedOption}
          {previewedOption}
        />

        <AudioInjector
          bind:this={audioInjectorRef}
          {currentPanel}
          on:injectAudio
          on:audioFileChange
        />

        <ResultInspector
          bind:this={resultInspectorRef}
          {currentPanel}
        />

        <BranchInspector
          {reputation}
          {pendingBranch}
          {branchHistory}
          on:resetReputation
          on:clearBranchHistory
          on:clearPendingBranch
        />

        <PanelJumpNav
          {story}
          {currentChapterIndex}
          {currentPanelIndex}
          on:jumpToPanel
        />
      </div>
    {/if}
  </div>
{/if}

<style>
  .dev-tools {
    position: fixed;
    top: 16px;
    right: 16px;
    z-index: 100;
  }

  .dev-btn {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    cursor: pointer;
    padding: 0;
    transition: background 0.15s;
  }

  .dev-btn:hover {
    background: rgba(255, 255, 255, 0.12);
  }

  .dev-btn svg {
    width: 16px;
    height: 16px;
    color: rgba(255, 255, 255, 0.35);
  }

  .dev-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.3);
    z-index: 99;
  }

  .dev-drawer {
    position: fixed;
    top: 0;
    right: 0;
    bottom: 0;
    width: 320px;
    max-width: 90vw;
    background: rgba(15, 15, 25, 0.97);
    backdrop-filter: blur(12px);
    border-left: 1px solid rgba(255, 255, 255, 0.1);
    padding: 16px;
    overflow-y: auto;
    z-index: 101;
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
</style>
