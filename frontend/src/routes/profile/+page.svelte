<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getApiBase } from '$lib/api';

  type Story = { id: string; title: string; subtitle?: string; language?: string };
  type Progress = {
    panel?: number;
    lives?: number;
    score?: number;
    state?: string;
    tutorialCompleted?: boolean;
    timestamp?: number;
  };

  const PROGRESS_KEY = 'LANGHERO_STORY_PROGRESS_V1';
  const LEVEL_KEY = 'LANGHERO_LEARNER_LEVEL';
  const API = getApiBase();

  let stories: Story[] = [];
  let progress: Record<string, Progress> = {};
  let learnerLevel = 'A2';
  let loaded = false;

  async function fetchStories() {
    try {
      const [p, s] = await Promise.all([
        fetch(`${API}/api/story-panels/stories`).then((r) => r.json()),
        fetch(`${API}/api/stories`).then((r) => r.json()),
      ]);
      stories = [...(p.stories || []), ...(s.stories || [])];
    } catch { stories = []; }
  }

  function loadProgress() {
    try {
      const saved = localStorage.getItem(PROGRESS_KEY);
      progress = saved ? JSON.parse(saved) : {};
      learnerLevel = localStorage.getItem(LEVEL_KEY) || 'A2';
    } catch { progress = {}; }
  }

  onMount(async () => {
    loadProgress();
    await fetchStories();
    loaded = true;
  });

  $: entries = stories
    .map((s) => ({ story: s, prog: progress[s.id] as Progress | undefined }))
    .filter((e) => e.prog); // only stories with any saved state
  $: untouched = stories.filter((s) => !progress[s.id]);
  $: totalLives = entries.reduce((n, e) => n + (e.prog?.lives ?? 0), 0);
  $: totalScore = entries.reduce((n, e) => n + (e.prog?.score ?? 0), 0);
</script>

<svelte:head><title>Profile — LangHero</title></svelte:head>

<main class="profile">
  <header>
    <button class="back" on:click={() => goto('/')}>← Home</button>
    <h1>Profile</h1>
    <p class="sub">Your learner level, per-story progress, and totals.</p>
  </header>

  <section class="level-row">
    <div class="level-pill">Level · <strong>{learnerLevel}</strong></div>
    <button class="change" on:click={() => goto('/settings')}>Change in Settings →</button>
  </section>

  <section class="totals">
    <div class="tile">
      <div class="tile-label">Total lives</div>
      <div class="tile-value">{totalLives}</div>
    </div>
    <div class="tile">
      <div class="tile-label">Total score</div>
      <div class="tile-value">{totalScore}</div>
    </div>
    <div class="tile">
      <div class="tile-label">Stories touched</div>
      <div class="tile-value">{entries.length}</div>
    </div>
  </section>

  <section>
    <h2>Per-story progress</h2>
    {#if !loaded}
      <p class="loading">Loading…</p>
    {:else if entries.length === 0}
      <p class="empty">No saves yet. Start a story from the home menu.</p>
    {:else}
      <div class="story-list">
        {#each entries as e}
          <button class="story-row" on:click={() => goto(`/play/story/${e.story.id}`)}>
            <div class="story-title">{e.story.title}</div>
            <div class="story-meta">
              <span>Lives <strong>{e.prog?.lives ?? '—'}</strong></span>
              <span>Score <strong>{e.prog?.score ?? 0}</strong></span>
              <span>Panel <strong>{e.prog?.panel ?? '—'}</strong></span>
              {#if e.prog?.state}<span class="state">{e.prog.state}</span>{/if}
              {#if e.prog?.timestamp}
                <span class="date">{new Date(e.prog.timestamp).toLocaleDateString()}</span>
              {/if}
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </section>

  {#if loaded && untouched.length > 0}
    <section>
      <h2>Not started</h2>
      <div class="story-list">
        {#each untouched as s}
          <button class="story-row dim" on:click={() => goto(`/play/story/${s.id}`)}>
            <div class="story-title">{s.title}</div>
            <div class="story-meta"><span>{s.subtitle || s.language || ''}</span></div>
          </button>
        {/each}
      </div>
    </section>
  {/if}
</main>

<style>
  .profile {
    min-height: 100vh;
    background: #050510;
    color: #e2e8f0;
    padding: 24px 16px 80px;
    font-family: system-ui, -apple-system, sans-serif;
    max-width: 700px;
    margin: 0 auto;
  }
  header { margin-bottom: 24px; }
  .back { background: none; border: none; color: #8b5cf6; cursor: pointer; font-size: 0.95rem; font-weight: 600; padding: 0 0 12px; }
  h1 { font-size: 1.8rem; margin: 0 0 4px; color: #f1f5f9; }
  .sub { color: #64748b; margin: 0; }

  .level-row { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 20px; }
  .level-pill { background: rgba(139,92,246,0.12); border: 1px solid rgba(139,92,246,0.3); color: #c4b5fd; padding: 8px 14px; border-radius: 999px; font-size: 0.9rem; }
  .level-pill strong { color: #e2e8f0; margin-left: 4px; }
  .change { background: none; border: none; color: #8b5cf6; cursor: pointer; font-size: 0.9rem; font-weight: 600; }

  .totals { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 32px; }
  .tile { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px; text-align: center; }
  .tile-label { color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.08em; }
  .tile-value { color: #f1f5f9; font-weight: 800; font-size: 1.6rem; margin-top: 4px; }

  section { margin-bottom: 28px; }
  h2 { font-size: 1.15rem; margin: 0 0 12px; color: #f1f5f9; }
  .loading, .empty { color: #64748b; font-style: italic; margin: 0; }

  .story-list { display: flex; flex-direction: column; gap: 8px; }
  .story-row { display: flex; flex-direction: column; gap: 4px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px 14px; cursor: pointer; text-align: left; color: inherit; transition: all 0.15s ease; }
  .story-row:hover { border-color: rgba(139,92,246,0.4); background: rgba(139,92,246,0.08); }
  .story-row.dim { opacity: 0.6; }
  .story-title { font-weight: 700; color: #f1f5f9; }
  .story-meta { display: flex; gap: 12px; font-size: 0.85rem; color: #94a3b8; flex-wrap: wrap; }
  .story-meta strong { color: #e2e8f0; }
  .state { color: #34d399; background: rgba(52,211,153,0.1); padding: 1px 6px; border-radius: 4px; font-size: 0.8rem; }
  .date { color: #64748b; }
</style>
