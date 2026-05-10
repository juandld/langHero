<script>
  import { createEventDispatcher } from 'svelte';
  import { RESPONSE_CATEGORIES } from '$lib/game/branchLogic';

  const dispatch = createEventDispatcher();

  export let currentPanel = null;
</script>

{#if currentPanel?.branch_point && currentPanel?.category_outcomes}
  <div class="dev-separator"></div>
  <div class="dev-title">Force Category</div>
  <div class="dev-force-cats">
    {#each Object.keys(currentPanel.category_outcomes) as catKey}
      {@const catInfo = RESPONSE_CATEGORIES[catKey]}
      {#if catInfo}
        <button
          class="dev-force-cat-btn"
          style="background: {catInfo.color}20; border-color: {catInfo.color}40; color: {catInfo.color}"
          on:click={() => dispatch('forceCategory', catKey)}
        >
          {catInfo.icon} {catInfo.label}
        </button>
      {/if}
    {/each}
  </div>
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

  .dev-force-cats {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .dev-force-cat-btn {
    padding: 3px 8px;
    border: 1px solid;
    border-radius: 5px;
    font-size: 0.65rem;
    font-weight: 600;
    cursor: pointer;
    transition: filter 0.15s;
  }

  .dev-force-cat-btn:hover {
    filter: brightness(1.3);
  }
</style>
