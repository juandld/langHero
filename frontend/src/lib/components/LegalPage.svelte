<script>
  /** @type {string} */
  export let title;
  /** @type {string} */
  export let updated = '2026-11-26';

  const links = [
    { href: '/pricing', label: 'Pricing' },
    { href: '/terms', label: 'Terms' },
    { href: '/privacy', label: 'Privacy' },
    { href: '/refund', label: 'Refunds' },
    { href: '/imprint', label: 'Imprint' },
    { href: '/takedown', label: 'Report content' }
  ];
</script>

<svelte:head>
  <title>{title} · LangHero</title>
</svelte:head>

<main class="legal">
  <h1>{title}</h1>
  <p class="draft">Draft, pending review. Last updated {updated}.</p>
  <slot />
  <nav class="legal-nav" aria-label="Legal pages">
    <a href="/">Home</a>
    {#each links as link}
      <a href={link.href}>{link.label}</a>
    {/each}
  </nav>
</main>

<style>
  .legal {
    max-width: 720px;
    margin: 0 auto;
    padding: 32px 20px 64px;
    line-height: 1.6;
    color: #1e293b;
  }
  .legal :global(h2) {
    margin-top: 1.8em;
    font-size: 1.2rem;
  }
  .legal :global(a) {
    color: #1d4ed8;
  }
  .legal :global(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
  }
  .legal :global(th),
  .legal :global(td) {
    border: 1px solid #cbd5e1;
    padding: 6px 8px;
    text-align: left;
    vertical-align: top;
  }
  .draft {
    color: #b45309;
    font-size: 0.9rem;
  }
  :global(mark.ph) {
    background: #fde68a;
    color: #1e293b;
    padding: 0 3px;
    border-radius: 3px;
  }
  .legal-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    margin-top: 48px;
    padding-top: 16px;
    border-top: 1px solid #cbd5e1;
    font-size: 0.9rem;
  }
</style>
