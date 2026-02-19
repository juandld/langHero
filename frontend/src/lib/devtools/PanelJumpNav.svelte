<script>
  import { createEventDispatcher } from 'svelte';
  import { RESPONSE_CATEGORIES, getOptionCategory } from '$lib/game/branchLogic';

  const dispatch = createEventDispatcher();

  export let story = null;
  export let currentChapterIndex = 0;
  export let currentPanelIndex = 0;

  let devClearBranchOnJump = false;

  $: devPanelTree = (() => {
    if (!story?.chapters) return [];

    const branchDestIds = new Set();
    const convergenceTargets = {};
    story.chapters.forEach(ch => {
      ch.panels.forEach(p => {
        if (p.branch_of) branchDestIds.add(p.id);
        if (p.branch_of && p.next_panel) {
          convergenceTargets[p.next_panel] = p.branch_of;
        }
      });
    });

    const tree = [];
    let num = 0;
    story.chapters.forEach((ch, ci) => {
      tree.push({ type: 'chapter', title: ch.title || `Chapter ${ci}`, chapterIdx: ci });

      ch.panels.forEach((p, pi) => {
        if (branchDestIds.has(p.id)) return;

        num++;
        const firstOpt = p.options?.[0] || null;
        const catColor = firstOpt ? getOptionCategory(firstOpt).color : null;

        if (p.branch_point && p.category_outcomes) {
          const branches = [];
          for (const [catKey, outcome] of Object.entries(p.category_outcomes)) {
            const tid = outcome.next_panel;
            if (!tid) continue;
            let tci = -1, tpi = -1, convergeTo = null;
            for (let sci = 0; sci < story.chapters.length; sci++) {
              const idx = story.chapters[sci].panels.findIndex(tp => tp.id === tid);
              if (idx >= 0) { tci = sci; tpi = idx; convergeTo = story.chapters[sci].panels[idx].next_panel || null; break; }
            }
            branches.push({ targetId: tid, categories: [catKey], chapterIdx: tci, panelIdx: tpi, convergeTo, lifeDelta: outcome.life_delta || 0 });
          }

          tree.push({
            type: 'branch-point', id: p.id, chapterIdx: ci, panelIdx: pi,
            hasOptions: p.options?.length > 0, catColor, num, branches,
          });
        } else {
          const fromId = convergenceTargets[p.id] || null;
          tree.push({
            type: fromId ? 'convergence' : 'panel',
            id: p.id, chapterIdx: ci, panelIdx: pi,
            hasOptions: p.options?.length > 0, catColor, num,
            ...(fromId ? { fromId } : {}),
          });
        }
      });
    });
    return tree;
  })();

  function devJumpToPanel(entry) {
    dispatch('jumpToPanel', { chapterIdx: entry.chapterIdx, panelIdx: entry.panelIdx, clearBranch: devClearBranchOnJump });
  }
</script>

<div class="dev-separator"></div>
<div class="dev-title">Panel Jump</div>
<label class="dev-option" style="margin-bottom:4px">
  <input type="checkbox" bind:checked={devClearBranchOnJump} />
  <span>Clear branch state on jump</span>
</label>
<div class="dev-panel-list">
  {#each devPanelTree as entry}
    {#if entry.type === 'chapter'}
      <div class="dev-chapter-header">── {entry.title} ──</div>
    {:else if entry.type === 'branch-point'}
      <button
        class="dev-panel-row dev-panel-row-branch-point"
        class:dev-panel-active={entry.chapterIdx === currentChapterIndex && entry.panelIdx === currentPanelIndex}
        on:click={() => devJumpToPanel(entry)}
      >
        <span class="dev-panel-idx">{entry.num}</span>
        <span class="dev-branch-point-icon">⑅</span>
        {#if entry.hasOptions}<span class="dev-panel-dot" style="background: {entry.catColor || '#6366f1'}"></span>{/if}
        <span class="dev-panel-id">{entry.id}</span>
      </button>
      <div class="dev-branch-children">
        {#each entry.branches as branch, bi}
          <button
            class="dev-branch-child"
            class:dev-branch-child-last={bi === entry.branches.length - 1}
            class:dev-panel-active={branch.chapterIdx === currentChapterIndex && branch.panelIdx === currentPanelIndex}
            on:click={() => devJumpToPanel(branch)}
          >
            <span class="dev-branch-rail">{bi === entry.branches.length - 1 ? '└' : '├'}</span>
            <span class="dev-branch-cats">{#each branch.categories as cat}{RESPONSE_CATEGORIES[cat]?.icon || '?'}{/each}</span>
            <span class="dev-panel-id">{branch.targetId}</span>
            {#if branch.lifeDelta}<span class="dev-branch-life">{branch.lifeDelta > 0 ? '+' : ''}{branch.lifeDelta}♥</span>{/if}
          </button>
        {/each}
      </div>
    {:else if entry.type === 'convergence'}
      <button
        class="dev-panel-row"
        class:dev-panel-active={entry.chapterIdx === currentChapterIndex && entry.panelIdx === currentPanelIndex}
        on:click={() => devJumpToPanel(entry)}
      >
        <span class="dev-panel-idx">{entry.num}</span>
        <span class="dev-convergence-icon">⇤</span>
        {#if entry.hasOptions}<span class="dev-panel-dot" style="background: {entry.catColor || '#6366f1'}"></span>{/if}
        <span class="dev-panel-id">{entry.id}</span>
      </button>
    {:else}
      <button
        class="dev-panel-row"
        class:dev-panel-active={entry.chapterIdx === currentChapterIndex && entry.panelIdx === currentPanelIndex}
        on:click={() => devJumpToPanel(entry)}
      >
        <span class="dev-panel-idx">{entry.num}</span>
        {#if entry.hasOptions}<span class="dev-panel-dot" style="background: {entry.catColor || '#6366f1'}"></span>{/if}
        <span class="dev-panel-id">{entry.id}</span>
      </button>
    {/if}
  {/each}
</div>

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

  .dev-panel-list {
    max-height: 50vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .dev-panel-row {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 3px 6px;
    background: none;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    text-align: left;
    color: #71717a;
    font-size: 0.6rem;
    transition: background 0.1s;
  }

  .dev-panel-row:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #a1a1aa;
  }

  .dev-panel-row.dev-panel-active {
    background: rgba(99, 102, 241, 0.2);
    color: #a5b4fc;
  }

  .dev-panel-idx {
    min-width: 18px;
    text-align: right;
    color: #3f3f46;
  }

  .dev-panel-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .dev-panel-id {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .dev-chapter-header {
    padding: 6px 6px 2px;
    font-size: 0.55rem;
    color: #52525b;
    letter-spacing: 0.03em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .dev-panel-row-branch-point {
    border-left: 2px solid #a78bfa;
  }

  .dev-branch-point-icon {
    color: #a78bfa;
    font-size: 0.7rem;
    flex-shrink: 0;
  }

  .dev-branch-children {
    padding-left: 24px;
    margin-left: 12px;
    border-left: 1px solid #3f3f46;
  }

  .dev-branch-child {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 2px 6px;
    background: none;
    border: none;
    cursor: pointer;
    text-align: left;
    color: #71717a;
    font-size: 0.6rem;
    transition: background 0.1s;
    position: relative;
    width: 100%;
  }

  .dev-branch-child:hover {
    background: rgba(255, 255, 255, 0.06);
    color: #a1a1aa;
  }

  .dev-branch-child.dev-panel-active {
    background: rgba(99, 102, 241, 0.2);
    color: #a5b4fc;
  }

  .dev-branch-child-last {
    border-left-color: transparent;
  }

  .dev-branch-life {
    margin-left: auto;
    font-size: 0.55rem;
    color: #fca5a5;
  }

  .dev-branch-rail {
    color: #3f3f46;
    flex-shrink: 0;
    font-family: monospace;
    font-size: 0.65rem;
    margin-left: -8px;
  }

  .dev-branch-cats {
    flex-shrink: 0;
    font-size: 0.65rem;
    min-width: 14px;
  }

  .dev-convergence-icon {
    color: #6ee7b7;
    font-size: 0.7rem;
    flex-shrink: 0;
  }
</style>
