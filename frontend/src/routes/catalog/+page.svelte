<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getApiBase } from '$lib/api';

  type PanelStory = { id: string; title: string; subtitle: string; chapter_count: number };
  type ScenarioStory = { id: string; title: string; language: string; description: string };
  type Practice = { id: string; title: string; description: string; target_language: string; register: string };
  type LegacyScene = {
    id: number;
    setting: string;
    description: string;
    character_dialogue_jp?: string;
    character_dialogue_en?: string;
    character_dialogue_mandarin?: string;
    mode?: string;
  };
  type DialogueLine = { speaker: string; text: string; sentiment?: string };

  const API = getApiBase();

  let panelStories: PanelStory[] = [];
  let scenarioStories: ScenarioStory[] = [];
  let practice: Practice[] = [];
  let legacy: LegacyScene[] = [];
  let dialogues: Record<string, Record<string, DialogueLine[]>> = {};
  let loading = true;
  let error = '';

  let expanded: Record<string, boolean> = {};
  function toggle(k: string) { expanded = { ...expanded, [k]: !expanded[k] }; }

  async function fetchJSON<T>(path: string): Promise<T> {
    const r = await fetch(`${API}${path}`);
    if (!r.ok) throw new Error(`${path} ${r.status}`);
    return r.json() as Promise<T>;
  }

  onMount(async () => {
    try {
      const [panels, stories, prac, leg] = await Promise.all([
        fetchJSON<{ stories: PanelStory[] }>('/api/story-panels/stories'),
        fetchJSON<{ stories: ScenarioStory[] }>('/api/stories'),
        fetchJSON<Practice[]>('/api/practice/scenarios'),
        fetchJSON<LegacyScene[]>('/api/scenarios'),
      ]);
      panelStories = panels.stories || [];
      scenarioStories = stories.stories || [];
      practice = prac || [];
      legacy = leg || [];

      const dialoguesByStory = await Promise.all(
        scenarioStories.map(async (s) => {
          try {
            const d = await fetchJSON<{ dialogues: Record<string, DialogueLine[]> }>(
              `/api/stories/${s.id}/dialogues`,
            );
            return [s.id, d.dialogues] as [string, Record<string, DialogueLine[]>];
          } catch {
            return [s.id, {}] as [string, Record<string, DialogueLine[]>];
          }
        }),
      );
      dialogues = Object.fromEntries(dialoguesByStory);
    } catch (e) {
      error = (e as Error).message;
    } finally {
      loading = false;
    }
  });

  function legacyArcs(items: LegacyScene[]) {
    const arcs: Record<string, LegacyScene[]> = { 'Tokyo ramen (1-8)': [], 'Shogun samurai (100-111)': [], 'Hong Kong (200-214)': [] };
    for (const s of items) {
      if (s.id < 100) arcs['Tokyo ramen (1-8)'].push(s);
      else if (s.id < 200) arcs['Shogun samurai (100-111)'].push(s);
      else arcs['Hong Kong (200-214)'].push(s);
    }
    return arcs;
  }

  $: arcs = legacyArcs(legacy);
  $: dialogueCount = Object.values(dialogues).reduce((n, byStory) => n + Object.keys(byStory).length, 0);
</script>

<svelte:head><title>Catalog — All Content</title></svelte:head>

<main class="catalog">
  <header>
    <button class="back" on:click={() => goto('/')}>← Home</button>
    <h1>All Content</h1>
    <p class="sub">Every storyline, scenario, and dialogue in the repo</p>
  </header>

  {#if loading}
    <p class="loading">Loading…</p>
  {:else if error}
    <p class="error">Failed to load: {error}</p>
  {:else}
    <!-- Panel stories -->
    <section>
      <h2>Panel stories <span class="count">{panelStories.length}</span></h2>
      <p class="hint">Visual novel format — image panels, chapters, time-freeze speaking.</p>
      <div class="grid">
        {#each panelStories as s}
          <button class="card" on:click={() => goto(`/play/story/${s.id}`)}>
            <div class="title">{s.title}</div>
            <div class="meta">{s.subtitle}</div>
            <div class="meta">{s.chapter_count} panels · <code>{s.id}</code></div>
            <div class="arrow">Play →</div>
          </button>
        {/each}
      </div>
    </section>

    <!-- Scenario stories -->
    <section>
      <h2>Scenario stories <span class="count">{scenarioStories.length}</span></h2>
      <p class="hint">Narrative branching via `/story?id=…` → StoryOrchestrator.</p>
      <div class="grid">
        {#each scenarioStories as s}
          <button
            class="card has-cover"
            on:click={() => goto(`/story?id=${s.id}&lang=${encodeURIComponent(s.language)}`)}
          >
            {#if s.cover_image}
              <img class="cover" src={s.cover_image} alt="" loading="lazy" />
            {/if}
            <div class="title">{s.title}</div>
            <div class="meta">{s.language}</div>
            <div class="meta">{s.description}</div>
            <div class="meta">
              <code>{s.id}</code>
              {#if dialogues[s.id]}
                · {Object.keys(dialogues[s.id]).length} dialogue scripts
              {/if}
            </div>
            <div class="arrow">Play →</div>
          </button>
        {/each}
      </div>
    </section>

    <!-- Practice scenarios -->
    <section>
      <h2>Practice scenarios <span class="count">{practice.length}</span></h2>
      <p class="hint">Live Jev-graded conversations via <code>/api/practice/chat</code>. Observability on.</p>
      <div class="grid">
        {#each practice as p}
          <button class="card" on:click={() => goto('/practice')}>
            <div class="title">{p.title}</div>
            <div class="meta">{p.target_language} · {p.register}</div>
            <div class="meta">{p.description}</div>
            <div class="meta"><code>{p.id}</code></div>
            <div class="arrow">Practice →</div>
          </button>
        {/each}
      </div>
    </section>

    <!-- Dialogue scripts -->
    <section>
      <h2>Dialogue scripts <span class="count">{dialogueCount}</span></h2>
      <p class="hint">
        Named dialogue sequences (intro, tutorials, drops). Pre-authored strings;
        inspection-only.
      </p>
      {#each Object.entries(dialogues) as [storyId, byKey]}
        {#if Object.keys(byKey).length > 0}
          <div class="group">
            <div class="group-title">{storyId}</div>
            {#each Object.entries(byKey) as [key, lines]}
              {@const panelKey = `d-${storyId}-${key}`}
              <div class="row">
                <button class="row-head" on:click={() => toggle(panelKey)}>
                  <span class="chev">{expanded[panelKey] ? '▾' : '▸'}</span>
                  <code>{key}</code>
                  <span class="row-meta">{lines.length} lines</span>
                </button>
                {#if expanded[panelKey]}
                  <ol class="lines">
                    {#each lines as line}
                      <li><strong>{line.speaker}:</strong> {line.text}</li>
                    {/each}
                  </ol>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      {/each}
    </section>

    <!-- Legacy narrative scenarios -->
    <section>
      <h2>Legacy narrative scenes <span class="count">{legacy.length}</span></h2>
      <p class="hint">
        Older <code>/narrative/interaction</code> content, three arcs. Pre-pivot;
        no live grading. Inspection-only here.
      </p>
      {#each Object.entries(arcs) as [arcName, items]}
        {@const key = `arc-${arcName}`}
        <div class="group">
          <button class="group-head" on:click={() => toggle(key)}>
            <span class="chev">{expanded[key] ? '▾' : '▸'}</span>
            <span class="group-title">{arcName}</span>
            <span class="row-meta">{items.length} scenes</span>
          </button>
          {#if expanded[key]}
            <table class="legacy-table">
              <thead><tr><th>ID</th><th>Setting</th><th>Dialogue</th></tr></thead>
              <tbody>
                {#each items as sc}
                  <tr>
                    <td><code>{sc.id}</code></td>
                    <td>{sc.setting}</td>
                    <td class="dlg">
                      {sc.character_dialogue_jp || sc.character_dialogue_mandarin || '—'}
                      {#if sc.character_dialogue_en}<div class="en">{sc.character_dialogue_en}</div>{/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {/if}
        </div>
      {/each}
    </section>
  {/if}
</main>

<style>
  .catalog {
    min-height: 100vh;
    background: #050510;
    color: #e2e8f0;
    padding: 24px 16px 80px;
    font-family: system-ui, -apple-system, sans-serif;
    max-width: 900px;
    margin: 0 auto;
  }
  header { margin-bottom: 32px; }
  .back {
    background: none; border: none; color: #8b5cf6; cursor: pointer;
    font-size: 0.95rem; font-weight: 600; padding: 0 0 12px;
  }
  h1 { font-size: 1.8rem; margin: 0 0 4px; color: #f1f5f9; }
  .sub { color: #64748b; margin: 0; }
  .loading, .error { color: #64748b; font-style: italic; }
  .error { color: #f87171; }

  section { margin-bottom: 40px; }
  h2 {
    font-size: 1.2rem; margin: 0 0 4px; color: #f1f5f9;
    display: flex; align-items: center; gap: 10px;
  }
  .count {
    font-size: 0.75rem; font-weight: 700; color: #c4b5fd;
    padding: 2px 8px; background: rgba(139, 92, 246, 0.15); border-radius: 999px;
  }
  .hint { color: #64748b; margin: 0 0 14px; font-size: 0.9rem; }
  .hint code { font-size: 0.85em; color: #94a3b8; background: rgba(255,255,255,0.05); padding: 1px 5px; border-radius: 4px; }

  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; }
  .card {
    display: flex; flex-direction: column; gap: 4px;
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px; padding: 14px; cursor: pointer; text-align: left;
    transition: all 0.15s ease; color: inherit;
  }
  .card:hover { border-color: rgba(139, 92, 246, 0.45); background: rgba(139, 92, 246, 0.08); }
  .card .cover {
    width: calc(100% + 28px); height: 110px; object-fit: cover;
    margin: -14px -14px 10px -14px; display: block; border-radius: 12px 12px 0 0;
  }
  .card .title { font-weight: 700; color: #f1f5f9; }
  .card .meta { font-size: 0.85rem; color: #94a3b8; }
  .card code { color: #c4b5fd; background: rgba(139,92,246,0.1); padding: 1px 4px; border-radius: 4px; font-size: 0.85em; }
  .card .arrow { margin-top: 6px; font-weight: 600; color: #8b5cf6; }

  .group { margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; overflow: hidden; }
  .group-head, .row-head {
    display: flex; align-items: center; gap: 8px;
    width: 100%; background: rgba(255,255,255,0.03); border: none;
    padding: 10px 14px; cursor: pointer; color: inherit; text-align: left;
  }
  .group-head:hover, .row-head:hover { background: rgba(139, 92, 246, 0.08); }
  .group-title { font-weight: 600; color: #e2e8f0; }
  .row { border-top: 1px solid rgba(255,255,255,0.05); }
  .row:first-child { border-top: none; }
  .row-meta { margin-left: auto; color: #64748b; font-size: 0.85rem; }
  .chev { color: #8b5cf6; font-size: 0.9rem; width: 1em; }

  .lines { margin: 0; padding: 10px 20px 14px 36px; color: #cbd5e1; font-size: 0.9rem; line-height: 1.5; }
  .lines li { margin: 2px 0; }
  .lines strong { color: #a78bfa; margin-right: 6px; }

  .legacy-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
  .legacy-table th { text-align: left; padding: 8px 14px; color: #64748b; background: rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.06); font-weight: 600; }
  .legacy-table td { padding: 8px 14px; border-bottom: 1px solid rgba(255,255,255,0.04); vertical-align: top; color: #cbd5e1; }
  .legacy-table code { color: #c4b5fd; }
  .legacy-table .dlg { max-width: 400px; }
  .legacy-table .en { color: #64748b; font-size: 0.85em; margin-top: 2px; }

  @media (max-width: 600px) {
    .grid { grid-template-columns: 1fr; }
    .legacy-table .dlg { max-width: 220px; }
  }
</style>
