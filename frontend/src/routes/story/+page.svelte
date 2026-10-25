<script>
  /**
   * Story Mode Entry Point
   *
   * This route provides the full narrative experience:
   *   intro → tutorial → transition → story_intro → drop → playing
   *
   * Default story is Shogun (Japanese).
   */
  import { StoryOrchestrator } from '$lib/components/story';
  import { page } from '$app/stores';

  $: storyId = $page.url.searchParams.get('id') || 'shogun';
  $: language = $page.url.searchParams.get('lang') || 'Japanese';
  $: pageTitle = `${storyId} · LangHero`;
</script>

<svelte:head><title>{pageTitle}</title></svelte:head>

<StoryOrchestrator {storyId} {language} />

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    overflow: hidden;
    background: #0f172a;
  }
</style>
