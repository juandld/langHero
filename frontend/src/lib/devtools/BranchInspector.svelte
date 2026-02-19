<script>
  import { createEventDispatcher } from 'svelte';
  import { RESPONSE_CATEGORIES } from '$lib/game/branchLogic';

  const dispatch = createEventDispatcher();

  export let reputation = {};
  export let pendingBranch = null;
  export let branchHistory = [];
</script>

<div class="dev-separator"></div>
<div class="dev-title">Reputation</div>
<div class="dev-rep-grid">
  {#each Object.entries(RESPONSE_CATEGORIES) as [key, cat]}
    <span class="dev-rep-icon" style="color: {cat.color}">{cat.icon}</span>
    <span class="dev-rep-label" style="color: {cat.color}">{reputation[key] || 0}</span>
  {/each}
</div>
<button class="dev-small-btn" on:click={() => dispatch('resetReputation')}>Reset Rep</button>

<div class="dev-separator"></div>
<div class="dev-title">Branch State</div>
{#if pendingBranch}
  <div class="dev-pending-branch">
    <span class="dev-pending-label">Pending</span>
    <span class="dev-pending-target">{pendingBranch.next_panel || '—'}</span>
    {#if pendingBranch.life_delta && pendingBranch.life_delta !== 0}
      <span class="dev-pending-life" style="color: {pendingBranch.life_delta < 0 ? '#fca5a5' : '#86efac'}">
        {pendingBranch.life_delta > 0 ? '+' : ''}{pendingBranch.life_delta} life
      </span>
    {/if}
    {#if pendingBranch.reputation_delta}
      <div class="dev-pending-rep-badges">
        {#each Object.entries(pendingBranch.reputation_delta) as [cat, delta]}
          {@const catInfo = RESPONSE_CATEGORIES[cat]}
          {#if catInfo}
            <span class="dev-rep-badge" style="color: {catInfo.color}; border-color: {catInfo.color}40">
              {catInfo.icon}{delta > 0 ? '+' : ''}{delta}
            </span>
          {/if}
        {/each}
      </div>
    {/if}
    <button class="dev-small-btn" on:click={() => dispatch('clearPendingBranch')}>Clear</button>
  </div>
{:else}
  <div class="dev-note">No pending branch</div>
{/if}

{#if branchHistory.length > 0}
  <div class="dev-branch-history">
    {#each [...branchHistory].reverse() as entry}
      {@const catInfo = RESPONSE_CATEGORIES[entry.category]}
      <div class="dev-history-entry">
        <span class="dev-history-panel">{entry.panelId}</span>
        {#if catInfo}
          <span class="dev-history-badge" style="background: {catInfo.color}20; color: {catInfo.color}">
            {catInfo.icon} {catInfo.label}
          </span>
        {/if}
      </div>
    {/each}
  </div>
  <button class="dev-small-btn" on:click={() => dispatch('clearBranchHistory')}>Clear History</button>
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

  .dev-note {
    font-size: 0.55rem;
    color: #52525b;
    font-style: italic;
    margin-top: 2px;
  }

  .dev-small-btn {
    padding: 2px 8px;
    font-size: 0.6rem;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 4px;
    color: #71717a;
    cursor: pointer;
    transition: background 0.15s;
  }

  .dev-small-btn:hover {
    background: rgba(255, 255, 255, 0.12);
    color: #a1a1aa;
  }

  .dev-rep-grid {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 4px;
  }

  .dev-rep-icon {
    font-size: 0.7rem;
  }

  .dev-rep-label {
    font-size: 0.7rem;
    font-weight: 600;
    margin-right: 4px;
  }

  .dev-pending-branch {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 6px;
    padding: 6px 8px;
    margin-bottom: 4px;
    font-size: 0.65rem;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4px;
  }

  .dev-pending-label {
    color: #6366f1;
    font-weight: 600;
    font-size: 0.6rem;
    text-transform: uppercase;
  }

  .dev-pending-target {
    color: #a5b4fc;
    font-weight: 600;
  }

  .dev-pending-life {
    font-weight: 600;
    font-size: 0.6rem;
  }

  .dev-pending-rep-badges {
    display: flex;
    gap: 3px;
  }

  .dev-rep-badge {
    font-size: 0.6rem;
    font-weight: 600;
    padding: 1px 4px;
    border: 1px solid;
    border-radius: 3px;
  }

  .dev-branch-history {
    max-height: 100px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin: 4px 0;
  }

  .dev-history-entry {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.6rem;
  }

  .dev-history-panel {
    color: #71717a;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 120px;
  }

  .dev-history-badge {
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 0.55rem;
    font-weight: 600;
    white-space: nowrap;
  }
</style>
