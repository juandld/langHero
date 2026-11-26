<script>
  import { fade } from 'svelte/transition';
  import { legalLinks } from '$lib/legalLinks.js';
</script>

<footer class="footer" in:fade={{ duration: 400, delay: 200 }}>
  <p class="version">Early Access</p>
  <nav class="legal-links" aria-label="Legal">
    {#each legalLinks as link}
      <a href={link.href}>{link.label}</a>
    {/each}
  </nav>
</footer>

<style>
  .footer {
    position: absolute;
    bottom: 24px;
    left: 0;
    right: 0;
    text-align: center;
  }
  .version {
    margin: 0;
    font-size: 0.85rem;
    color: #475569;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }
  .legal-links {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 6px 16px;
    margin-top: 8px;
    font-size: 0.8rem;
  }
  .legal-links a {
    color: #64748b;
    text-decoration: none;
  }
  .legal-links a:hover {
    color: #94a3b8;
    text-decoration: underline;
  }
</style>
