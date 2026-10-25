<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  const LEVEL_KEY = 'LANGHERO_LEARNER_LEVEL';
  const AUTO_NARRATE_KEY = 'autoNarrate';
  const VOICE_SPEED_KEY = 'LANGHERO_VOICE_SPEED';

  const LEVELS = [
    { id: 'A1', label: 'A1 — beginner', hint: 'first weeks; survival phrases' },
    { id: 'A2', label: 'A2 — basic', hint: 'simple everyday exchanges' },
    { id: 'B1', label: 'B1 — intermediate', hint: 'can handle most travel situations' },
    { id: 'B2', label: 'B2 — upper intermediate', hint: 'spontaneous conversation' },
    { id: 'C1', label: 'C1 — advanced', hint: 'fluent, nuanced' },
  ];

  let learnerLevel = 'A2';
  let autoNarrate = true;
  let voiceSpeed = 1.0;
  let saved = false;

  onMount(() => {
    try {
      learnerLevel = localStorage.getItem(LEVEL_KEY) || 'A2';
      autoNarrate = localStorage.getItem(AUTO_NARRATE_KEY) !== 'false';
      voiceSpeed = parseFloat(localStorage.getItem(VOICE_SPEED_KEY) || '1.0');
    } catch { /* localStorage unavailable */ }
  });

  function save() {
    try {
      localStorage.setItem(LEVEL_KEY, learnerLevel);
      localStorage.setItem(AUTO_NARRATE_KEY, String(autoNarrate));
      localStorage.setItem(VOICE_SPEED_KEY, String(voiceSpeed));
      saved = true;
      setTimeout(() => (saved = false), 1500);
    } catch {
      saved = false;
    }
  }
</script>

<svelte:head><title>Settings — LangHero</title></svelte:head>

<main class="settings">
  <header>
    <button class="back" on:click={() => goto('/')}>← Home</button>
    <h1>Settings</h1>
    <p class="sub">Choose how practice and story playback behave.</p>
  </header>

  <section>
    <h2>Learner level</h2>
    <p class="hint">
      Used to grade whether tutor lines are appropriately challenging. Changing
      this won't restart your current story.
    </p>
    <div class="radios">
      {#each LEVELS as lv}
        <label class="radio" class:selected={learnerLevel === lv.id}>
          <input type="radio" bind:group={learnerLevel} value={lv.id} />
          <div>
            <div class="radio-label">{lv.label}</div>
            <div class="radio-hint">{lv.hint}</div>
          </div>
        </label>
      {/each}
    </div>
  </section>

  <section>
    <h2>Audio</h2>
    <label class="toggle">
      <input type="checkbox" bind:checked={autoNarrate} />
      <span>Auto-narrate new panels</span>
    </label>
    <label class="slider-row">
      <span>Voice speed <code>{voiceSpeed.toFixed(2)}×</code></span>
      <input
        type="range" min="0.5" max="2.0" step="0.05" bind:value={voiceSpeed}
      />
    </label>
  </section>

  <div class="save-row">
    <button class="save" on:click={save}>Save</button>
    {#if saved}
      <span class="saved">Saved ✓</span>
    {/if}
  </div>
</main>

<style>
  .settings {
    min-height: 100vh;
    background: #050510;
    color: #e2e8f0;
    padding: 24px 16px 80px;
    font-family: system-ui, -apple-system, sans-serif;
    max-width: 700px;
    margin: 0 auto;
  }
  header { margin-bottom: 32px; }
  .back {
    background: none; border: none; color: #8b5cf6;
    cursor: pointer; font-size: 0.95rem; font-weight: 600;
    padding: 0 0 12px;
  }
  h1 { font-size: 1.8rem; margin: 0 0 4px; color: #f1f5f9; }
  .sub { color: #64748b; margin: 0; }

  section { margin-bottom: 36px; }
  h2 { font-size: 1.1rem; margin: 0 0 4px; color: #f1f5f9; }
  .hint { color: #64748b; margin: 0 0 14px; font-size: 0.9rem; }

  .radios { display: flex; flex-direction: column; gap: 8px; }
  .radio {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 12px 14px;
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; cursor: pointer;
  }
  .radio:hover { border-color: rgba(139,92,246,0.4); }
  .radio.selected { border-color: #8b5cf6; background: rgba(139,92,246,0.1); }
  .radio input { margin-top: 3px; accent-color: #8b5cf6; }
  .radio-label { font-weight: 600; color: #f1f5f9; }
  .radio-hint { font-size: 0.85rem; color: #94a3b8; }

  .toggle {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 0; cursor: pointer; color: #e2e8f0;
  }
  .toggle input { accent-color: #8b5cf6; width: 18px; height: 18px; }

  .slider-row {
    display: flex; flex-direction: column; gap: 6px;
    padding: 10px 0; color: #e2e8f0;
  }
  .slider-row code {
    background: rgba(255,255,255,0.05); padding: 1px 6px;
    border-radius: 4px; color: #c4b5fd; margin-left: 6px;
  }
  .slider-row input { accent-color: #8b5cf6; width: 100%; }

  .save-row { display: flex; align-items: center; gap: 12px; margin-top: 16px; }
  .save {
    background: linear-gradient(135deg, rgba(139,92,246,0.4), rgba(99,102,241,0.4));
    border: 1px solid rgba(139,92,246,0.6);
    color: #fff; font-weight: 700; padding: 10px 20px;
    border-radius: 10px; cursor: pointer;
  }
  .save:hover { background: rgba(139,92,246,0.5); }
  .saved { color: #34d399; font-weight: 600; }
</style>
