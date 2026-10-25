<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getApiBase } from '$lib/api';

  type Scores = { register_fits?: number; naturalness?: number; level_appropriate?: number };
  type GradeRow = {
    id: number; ts: string; grader: string; target_language: string;
    scores: Scores; latency_ms: number;
    tutor_line: string; source_id: string | null;
    scenario: string; speaker: string | null; session_id: string | null;
  };
  type Stats = { grader: string; count_7d: number; latency_ms_avg: number; scores_avg_last_100: Scores };

  const API = getApiBase();

  let rows: GradeRow[] = [];
  let stats: Stats[] = [];
  let graderFilter = '';
  let loading = true;
  let error = '';

  async function reload() {
    loading = true;
    error = '';
    try {
      const q = new URLSearchParams();
      if (graderFilter) q.set('grader', graderFilter);
      q.set('limit', '150');
      const [g, s] = await Promise.all([
        fetch(`${API}/api/observability/grades?${q}`).then((r) => r.json()),
        fetch(`${API}/api/observability/grades/stats`).then((r) => r.json()),
      ]);
      rows = g.rows || [];
      stats = s.by_grader || [];
    } catch (e) {
      error = (e as Error).message;
    } finally {
      loading = false;
    }
  }

  function colour(score: number | undefined): string {
    if (score == null) return '#64748b';
    if (score >= 0.75) return '#34d399';
    if (score >= 0.55) return '#fbbf24';
    return '#f87171';
  }

  onMount(reload);

  $: graders = Array.from(new Set(stats.map((s) => s.grader)));
</script>

<svelte:head><title>Observability — Jev grades</title></svelte:head>

<main class="obs">
  <header>
    <button class="back" on:click={() => goto('/')}>← Home</button>
    <h1>Observability</h1>
    <p class="sub">Jev grade log — recent rows and per-grader roll-ups.</p>
  </header>

  <section>
    <h2>Per-grader stats <span class="hint">(last 7 days · dim avg from last 100 rows)</span></h2>
    {#if stats.length === 0 && !loading}
      <p class="empty">No grades logged yet.</p>
    {:else}
      <div class="stats-grid">
        {#each stats as s}
          <button
            class="stat-tile"
            class:active={graderFilter === s.grader}
            on:click={() => { graderFilter = graderFilter === s.grader ? '' : s.grader; reload(); }}
          >
            <div class="stat-grader">{s.grader}</div>
            <div class="stat-count">{s.count_7d} rows · {s.latency_ms_avg}ms avg</div>
            <div class="stat-dims">
              <span style="color:{colour(s.scores_avg_last_100.register_fits)}">reg {s.scores_avg_last_100.register_fits?.toFixed(2)}</span>
              <span style="color:{colour(s.scores_avg_last_100.naturalness)}">nat {s.scores_avg_last_100.naturalness?.toFixed(2)}</span>
              <span style="color:{colour(s.scores_avg_last_100.level_appropriate)}">lvl {s.scores_avg_last_100.level_appropriate?.toFixed(2)}</span>
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </section>

  <section>
    <h2>
      Recent grades
      {#if graderFilter}
        <span class="pill">filter: {graderFilter}
          <button class="clear" on:click={() => { graderFilter = ''; reload(); }}>✕</button>
        </span>
      {/if}
    </h2>
    {#if loading}
      <p class="empty">Loading…</p>
    {:else if error}
      <p class="error">Failed: {error}</p>
    {:else if rows.length === 0}
      <p class="empty">No matching grades.</p>
    {:else}
      <table class="grades">
        <thead>
          <tr>
            <th>ts</th><th>grader</th><th>reg</th><th>nat</th><th>lvl</th>
            <th>line</th><th>source</th><th>ms</th>
          </tr>
        </thead>
        <tbody>
          {#each rows as r}
            <tr>
              <td class="ts">{r.ts.replace('T', ' ').slice(0, 19)}</td>
              <td><code>{r.grader}</code></td>
              <td style="color:{colour(r.scores.register_fits)}">{r.scores.register_fits?.toFixed(2) ?? '—'}</td>
              <td style="color:{colour(r.scores.naturalness)}">{r.scores.naturalness?.toFixed(2) ?? '—'}</td>
              <td style="color:{colour(r.scores.level_appropriate)}">{r.scores.level_appropriate?.toFixed(2) ?? '—'}</td>
              <td class="line">{r.tutor_line.slice(0, 50)}</td>
              <td class="src"><code>{r.source_id || '—'}</code></td>
              <td class="lat">{r.latency_ms}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>
</main>

<style>
  .obs { min-height: 100vh; background: #050510; color: #e2e8f0; padding: 24px 16px 80px; font-family: system-ui,-apple-system,sans-serif; max-width: 1100px; margin: 0 auto; }
  header { margin-bottom: 28px; }
  .back { background: none; border: none; color: #8b5cf6; cursor: pointer; font-size: 0.95rem; font-weight: 600; padding: 0 0 12px; }
  h1 { font-size: 1.8rem; margin: 0 0 4px; color: #f1f5f9; }
  .sub { color: #64748b; margin: 0; }

  section { margin-bottom: 32px; }
  h2 { font-size: 1.1rem; margin: 0 0 10px; color: #f1f5f9; display: flex; align-items: center; gap: 10px; }
  .hint { color: #64748b; font-weight: 400; font-size: 0.85rem; }
  .empty, .error { color: #64748b; font-style: italic; margin: 0; }
  .error { color: #f87171; font-style: normal; }
  .pill { font-size: 0.75rem; color: #c4b5fd; background: rgba(139,92,246,0.15); padding: 2px 8px; border-radius: 999px; display: inline-flex; align-items: center; gap: 6px; }
  .clear { background: none; border: none; color: inherit; cursor: pointer; padding: 0; font-size: 1em; }

  .stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 10px; }
  .stat-tile { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px 14px; text-align: left; cursor: pointer; color: inherit; transition: all 0.15s; }
  .stat-tile:hover { border-color: rgba(139,92,246,0.4); }
  .stat-tile.active { border-color: #8b5cf6; background: rgba(139,92,246,0.1); }
  .stat-grader { font-weight: 700; color: #f1f5f9; font-family: ui-monospace, monospace; font-size: 0.95rem; }
  .stat-count { color: #94a3b8; font-size: 0.85rem; margin-top: 2px; }
  .stat-dims { display: flex; gap: 10px; font-size: 0.85rem; margin-top: 6px; font-family: ui-monospace, monospace; }

  table.grades { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
  table.grades th { text-align: left; padding: 8px 10px; color: #64748b; background: rgba(255,255,255,0.03); border-bottom: 1px solid rgba(255,255,255,0.06); font-weight: 600; }
  table.grades td { padding: 6px 10px; border-bottom: 1px solid rgba(255,255,255,0.04); color: #cbd5e1; vertical-align: top; }
  table.grades td code { color: #c4b5fd; background: rgba(139,92,246,0.08); padding: 1px 5px; border-radius: 3px; font-size: 0.85em; }
  td.ts { color: #94a3b8; font-family: ui-monospace, monospace; font-size: 0.78rem; white-space: nowrap; }
  td.line { max-width: 300px; }
  td.src { font-family: ui-monospace, monospace; font-size: 0.78rem; }
  td.lat { color: #64748b; text-align: right; font-family: ui-monospace, monospace; font-size: 0.78rem; }

  @media (max-width: 700px) {
    table.grades { font-size: 0.78rem; }
    td.line { max-width: 160px; }
  }
</style>
