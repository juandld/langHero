<script lang="ts">
  import { page } from '$app/stores';
  import Breadcrumbs from '$lib/components/Breadcrumbs.svelte';
  import ProfileBadge from '$lib/components/ProfileBadge.svelte';

  // Primary nav: core user destinations (not dev tools). "Browse" is the
  // canonical content index for the project — stories, scenarios, practice,
  // dialogue scripts — not a side-door "all content" page.
  const links = [
    { href: '/', label: 'Menu' },
    { href: '/catalog', label: 'Browse' },
    { href: '/profile', label: 'Profile' },
    { href: '/settings', label: 'Settings' },
    { href: '/login', label: 'Login' },
  ];

  $: path = $page?.url?.pathname || '/';
  function isActive(href: string) {
    if (href === '/') return path === '/';
    return path === href || path.startsWith(`${href}/`);
  }
</script>

<header class="topnav">
  <div class="inner">
    <a class="brand" href="/" aria-label="LangHero menu">LangHero</a>
    <div class="profile-section">
      <ProfileBadge compact />
    </div>
    <nav class="nav" aria-label="Primary">
      {#each links as l (l.href)}
        <a class={`link ${isActive(l.href) ? 'active' : ''}`} href={l.href}>{l.label}</a>
      {/each}
    </nav>
  </div>
  <Breadcrumbs />
</header>

<style>
  .topnav {
    position: sticky;
    top: 0;
    z-index: 9000;
    background: rgba(255, 255, 255, 0.92);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid #e2e8f0;
  }

  .inner {
    max-width: 980px;
    margin: 0 auto;
    padding: 10px 14px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
  }

  .brand {
    color: #0f172a;
    text-decoration: none;
    font-weight: 950;
    letter-spacing: -0.02em;
    padding: 8px 10px;
    border-radius: 12px;
  }

  .brand:hover {
    background: #f8fafc;
  }

  .profile-section {
    flex: 1;
    display: flex;
    justify-content: center;
  }

  .nav {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .link {
    color: #0f172a;
    text-decoration: none;
    font-weight: 850;
    padding: 8px 10px;
    border-radius: 12px;
    border: 1px solid transparent;
  }

  .link:hover {
    background: #f8fafc;
    border-color: #e2e8f0;
  }

  .link.active {
    background: #0f172a;
    color: #fff;
    border-color: #0f172a;
  }

  /* Mobile: let items shrink + nowrap so the nav stays as a single row
     instead of each link falling onto its own line. Tight padding/font so
     all 5 primary items visibly fit on a 375px viewport. */
  @media (max-width: 640px) {
    .inner { padding: 6px 8px; gap: 4px; }
    .brand { padding: 4px 6px; font-size: 0.9rem; }
    .profile-section { flex: 0 1 auto; justify-content: flex-start; }
    .nav { flex-wrap: nowrap; gap: 2px; overflow-x: auto; -webkit-overflow-scrolling: touch; }
    .link { padding: 4px 6px; font-size: 0.75rem; font-weight: 700; flex-shrink: 0; letter-spacing: -0.01em; }
    /* Hide the profile pill on very narrow screens — it duplicates the Profile
       link below and eats horizontal space nav items need. */
    .profile-section :global(.profile-badge-compact) { display: none; }
  }

  @media (max-width: 400px) {
    .profile-section { display: none; }
    .brand { font-size: 0.85rem; }
  }
</style>
