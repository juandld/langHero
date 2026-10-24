<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { fade, fly, scale } from 'svelte/transition';
  import { cubicOut } from 'svelte/easing';
  import { runsStore, syncFromStorage } from '$lib/runStore.js';
  import { authUser, hydrateAuth, isAppwriteConfigured } from '$lib/auth';
  import { getBackendUrl } from '$lib/config';

  let mounted = false;
  let showTitle = false;
  let showMenu = false;
  let showParticles = false;

  // Data
  let stories = [];
  let storyProgress = {};
  let storiesLoaded = false;

  // Sub-views
  let view = 'main'; // 'main' | 'continue' | 'newgame' | 'practice'

  // Auth
  let authChecked = false;
  $: isLoggedIn = $authUser !== null;

  const STORY_PROGRESS_KEY = 'LANGHERO_STORY_PROGRESS_V1';

  function loadStoryProgress() {
    try {
      const saved = localStorage.getItem(STORY_PROGRESS_KEY);
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  }

  async function fetchStories() {
    try {
      // Fetch visual novel stories (story-panels system)
      const panelRes = await fetch(`${getBackendUrl()}/api/story-panels/stories`);
      const panelData = await panelRes.json();
      const panelStories = (panelData.stories || []).map(s => ({
        ...s,
        type: 'panels',
        language: s.subtitle || '',
      }));

      // Fetch scenario-based stories
      const scenarioRes = await fetch(`${getBackendUrl()}/api/stories`);
      const scenarioData = await scenarioRes.json();
      const scenarioStories = (scenarioData.stories || []).map(s => ({
        ...s,
        type: 'scenarios',
      }));

      // Panel stories first, then scenario stories (avoid duplicates by language)
      stories = [...panelStories, ...scenarioStories];
    } catch (e) {
      console.warn('Failed to fetch stories:', e);
      stories = [];
    }
    storiesLoaded = true;
  }

  // Combine story metadata with progress
  $: saveSlots = stories
    .map((s) => {
      const prog = storyProgress[s.id];
      if (
        !prog ||
        (!prog.tutorialCompleted &&
          prog.state !== 'playing' &&
          prog.state !== 'tutorial')
      )
        return null;
      return {
        ...s,
        progress: prog,
        lastPlayed: prog.timestamp
          ? new Date(prog.timestamp).toLocaleDateString()
          : 'Unknown',
        stateLabel:
          prog.state === 'playing'
            ? 'In Progress'
            : prog.tutorialCompleted
              ? 'Tutorial Done'
              : 'Started',
      };
    })
    .filter(Boolean);

  $: hasSaves = saveSlots.length > 0;

  const languages = [
    {
      id: 'mandarin',
      label: 'Mandarin Chinese',
      desc: 'Practical spoken Mandarin for Hong Kong',
    },
    {
      id: 'japanese',
      label: 'Japanese',
      desc: 'Survive feudal Japan as a shipwrecked stranger',
    },
    {
      id: 'spanish',
      label: 'Spanish',
      desc: 'Follow Manuela Sáenz through revolutionary Quito',
    },
  ];

  onMount(async () => {
    syncFromStorage();
    mounted = true;

    if (isAppwriteConfigured()) {
      try {
        await hydrateAuth();
      } catch {
        // Auth failed, continue as logged out
      }
    }
    authChecked = true;
    storyProgress = loadStoryProgress();

    await fetchStories();

    setTimeout(() => (showParticles = true), 50);
    setTimeout(() => (showTitle = true), 200);
    setTimeout(() => (showMenu = true), 600);
  });

  function storyUrl(story) {
    if (story.type === 'panels') {
      return `/play/story/${story.id}`;
    }
    return `/story?id=${story.id}&lang=${encodeURIComponent(story.language)}`;
  }

  function continueStory(storyId) {
    const story = stories.find((s) => s.id === storyId);
    if (story) goto(storyUrl(story));
  }

  function startNewStory(storyId) {
    const story = stories.find((s) => s.id === storyId);
    if (story) {
      try {
        const progress = loadStoryProgress();
        delete progress[storyId];
        localStorage.setItem(STORY_PROGRESS_KEY, JSON.stringify(progress));
      } catch {
        // ignore
      }
      goto(storyUrl(story));
    }
  }

  function startPractice(langId) {
    const lang = languages.find((l) => l.id === langId);
    const story = stories.find((s) =>
      s.language.toLowerCase().includes(langId),
    );
    if (story && story.tutorial?.scenarios?.length) {
      goto(
        `/demo?lang=${encodeURIComponent(lang?.label || langId)}&start=${story.tutorial.scenarios[0]}`,
      );
    } else {
      goto(`/demo?lang=${encodeURIComponent(lang?.label || langId)}`);
    }
  }

  const floatingChars = ['時', '旅', '学', '你', '好', '说', '听', '道'];
  const particles = Array.from({ length: 20 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: 2 + Math.random() * 4,
    duration: 15 + Math.random() * 20,
    delay: Math.random() * 10,
    opacity: 0.2 + Math.random() * 0.4,
  }));
</script>

<svelte:head>
  <title>LangHero - Learn Through Time</title>
</svelte:head>

<main class="main-menu">
  <!-- Background -->
  <div class="bg-layer bg-stars"></div>
  <div class="bg-layer bg-nebula"></div>
  <div class="bg-layer bg-vignette"></div>

  {#if showParticles}
    <div class="particles-container" in:fade={{ duration: 2000 }}>
      {#each particles as p (p.id)}
        <div
          class="particle"
          style="left:{p.x}%;top:{p.y}%;width:{p.size}px;height:{p.size}px;opacity:{p.opacity};animation-duration:{p.duration}s;animation-delay:{p.delay}s;"
        ></div>
      {/each}
    </div>
    <div class="kanji-container">
      {#each floatingChars as ch, i}
        <div
          class="floating-kanji"
          style="left:{10 + i * 11}%;animation-delay:{i * 2}s;animation-duration:{25 + i * 3}s;"
        >
          {ch}
        </div>
      {/each}
    </div>
  {/if}

  <div class="content">
    <!-- Title -->
    {#if showTitle}
      <div
        class="title-container"
        in:fly={{ y: -30, duration: 600, easing: cubicOut }}
      >
        <h1 class="game-title">
          <span class="title-lang">Lang</span><span class="title-hero"
            >Hero</span
          >
        </h1>
      </div>
      <p class="tagline" in:fade={{ duration: 400 }}>Learn Through Time</p>
    {/if}

    <!-- Main Menu -->
    {#if showMenu && view === 'main'}
      <nav class="menu-options" in:fade={{ duration: 400 }}>
        <!-- Continue (if has saves) -->
        {#if hasSaves}
          <button
            class="menu-btn primary"
            on:click={() => (view = 'continue')}
            in:fly={{ y: 20, duration: 400 }}
          >
            <span class="btn-icon"
              ><svg viewBox="0 0 24 24" fill="currentColor"
                ><path d="M8 5v14l11-7z" /></svg
              ></span
            >
            <span class="btn-text">
              <span class="btn-label">Continue</span>
              <span class="btn-subtitle"
                >{saveSlots.length} story{saveSlots.length !== 1
                  ? ' saves'
                  : ' save'}</span
              >
            </span>
            <span class="btn-arrow">→</span>
          </button>
        {/if}

        <!-- Begin New -->
        <button
          class="menu-btn {hasSaves ? 'secondary' : 'primary'}"
          on:click={() => (view = 'newgame')}
          in:fly={{ y: 20, duration: 400, delay: 80 }}
        >
          <span class="btn-icon"
            ><svg viewBox="0 0 24 24" fill="currentColor"
              ><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" /></svg
            ></span
          >
          <span class="btn-text">
            <span class="btn-label">Begin New</span>
            <span class="btn-subtitle">Choose a story</span>
          </span>
          <span class="btn-arrow">→</span>
        </button>

        <!-- Quick Practice -->
        <button
          class="menu-btn tertiary"
          on:click={() => (view = 'practice')}
          in:fly={{ y: 20, duration: 400, delay: 160 }}
        >
          <span class="btn-icon"
            ><svg viewBox="0 0 24 24" fill="currentColor"
              ><path
                d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"
              /></svg
            ></span
          >
          <span class="btn-text">
            <span class="btn-label">Quick Practice</span>
            <span class="btn-subtitle">Jump in, pick a language</span>
          </span>
          <span class="btn-arrow">→</span>
        </button>

        <div
          class="menu-divider"
          in:fly={{ y: 20, duration: 400, delay: 240 }}
        ></div>

        <!-- Browse all content -->
        <button
          class="menu-btn compact"
          on:click={() => goto('/catalog')}
          in:fly={{ y: 20, duration: 400, delay: 260 }}
        >
          <span class="btn-icon small"
            ><svg viewBox="0 0 24 24" fill="currentColor"
              ><path d="M3 5h18v2H3V5zm0 6h18v2H3v-2zm0 6h18v2H3v-2z" /></svg
            ></span
          >
          <span class="btn-text"
            ><span class="btn-label">Browse Stories</span></span
          >
        </button>

        <!-- Settings -->
        <button
          class="menu-btn compact"
          on:click={() => goto('/settings')}
          in:fly={{ y: 20, duration: 400, delay: 270 }}
        >
          <span class="btn-icon small"
            ><svg viewBox="0 0 24 24" fill="currentColor"
              ><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 00.12-.61l-1.92-3.32a.488.488 0 00-.59-.22l-2.39.96a7.013 7.013 0 00-1.62-.94l-.36-2.54a.484.484 0 00-.48-.41h-3.84a.48.48 0 00-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96a.46.46 0 00-.57.22L2.74 8.87a.49.49 0 00.12.61l2.03 1.58c-.05.3-.07.62-.07.94 0 .32.02.64.07.94l-2.03 1.58a.49.49 0 00-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.26.41.5.41h3.84c.24 0 .45-.17.5-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32a.49.49 0 00-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" /></svg
            ></span
          >
          <span class="btn-text"
            ><span class="btn-label">Settings</span></span
          >
        </button>

        <!-- Import -->
        <button
          class="menu-btn compact"
          on:click={() => goto('/import')}
          in:fly={{ y: 20, duration: 400, delay: 280 }}
        >
          <span class="btn-icon small"
            ><svg viewBox="0 0 24 24" fill="currentColor"
              ><path
                d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z"
              /></svg
            ></span
          >
          <span class="btn-text"
            ><span class="btn-label">Import Story</span></span
          >
        </button>

        <!-- Account -->
        <button
          class="menu-btn compact"
          on:click={() => goto('/login')}
          in:fly={{ y: 20, duration: 400, delay: 320 }}
        >
          <span class="btn-icon small"
            ><svg viewBox="0 0 24 24" fill="currentColor"
              ><path
                d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
              /></svg
            ></span
          >
          <span class="btn-text"
            ><span class="btn-label">Account</span></span
          >
        </button>
      </nav>
    {/if}

    <!-- Continue: Story Slots -->
    {#if showMenu && view === 'continue'}
      <div class="sub-view" in:fly={{ x: 40, duration: 300 }}>
        <button class="back-btn" on:click={() => (view = 'main')}
          >← Back</button
        >
        <h2 class="sub-title">Continue</h2>
        <div class="card-list">
          {#each saveSlots as slot}
            <button class="story-card" on:click={() => continueStory(slot.id)}>
              <div class="card-lang">{slot.language}</div>
              <div class="card-title">{slot.title}</div>
              <div class="card-meta">
                <span class="card-state">{slot.stateLabel}</span>
                <span class="card-date">{slot.lastPlayed}</span>
              </div>
              <div class="card-desc">{slot.description}</div>
              <div class="card-arrow">Resume →</div>
            </button>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Begin New: Story Picker -->
    {#if showMenu && view === 'newgame'}
      <div class="sub-view" in:fly={{ x: 40, duration: 300 }}>
        <button class="back-btn" on:click={() => (view = 'main')}
          >← Back</button
        >
        <h2 class="sub-title">Choose a Story</h2>
        <div class="card-list">
          {#if storiesLoaded}
            {#each stories as story}
              <button
                class="story-card"
                on:click={() => startNewStory(story.id)}
              >
                <div class="card-lang">{story.language}</div>
                <div class="card-title">{story.title}</div>
                <div class="card-desc">{story.description || story.subtitle || ''}</div>
                <div class="card-meta">
                  {#if story.chapter_count}
                    <span class="card-state">{story.chapter_count} chapters</span>
                  {:else if story.main?.chapters?.length}
                    <span class="card-state">{story.main.chapters.length} chapters</span>
                  {/if}
                  {#if story.type === 'panels'}
                    <span class="card-badge">Visual Novel</span>
                  {/if}
                </div>
                <div class="card-arrow">Start →</div>
              </button>
            {/each}
          {:else}
            <p class="loading-text">Loading stories...</p>
          {/if}
        </div>
      </div>
    {/if}

    <!-- Quick Practice: Language Picker -->
    {#if showMenu && view === 'practice'}
      <div class="sub-view" in:fly={{ x: 40, duration: 300 }}>
        <button class="back-btn" on:click={() => (view = 'main')}
          >← Back</button
        >
        <h2 class="sub-title">Pick a Language</h2>
        <div class="card-list">
          {#each languages as lang}
            <button
              class="story-card"
              on:click={() => startPractice(lang.id)}
            >
              <div class="card-lang">{lang.label}</div>
              <div class="card-desc">{lang.desc}</div>
              <div class="card-arrow">Practice →</div>
            </button>
          {/each}
        </div>
      </div>
    {/if}
  </div>

  <!-- Footer -->
  {#if showMenu}
    <footer class="footer" in:fade={{ duration: 400, delay: 200 }}>
      <p class="version">Early Access</p>
    </footer>
  {/if}
</main>

<style>
  .main-menu {
    position: fixed;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    overflow-y: auto;
    background: #050510;
    font-family:
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      'Segoe UI',
      sans-serif;
  }

  /* Background */
  .bg-layer {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }
  .bg-stars {
    background:
      radial-gradient(1px 1px at 20% 30%, rgba(255, 255, 255, 0.8), transparent),
      radial-gradient(1px 1px at 40% 70%, rgba(255, 255, 255, 0.6), transparent),
      radial-gradient(
        2px 2px at 60% 20%,
        rgba(255, 255, 255, 0.7),
        transparent
      ),
      radial-gradient(1px 1px at 80% 40%, rgba(255, 255, 255, 0.5), transparent),
      radial-gradient(
        1px 1px at 90% 80%,
        rgba(255, 255, 255, 0.4),
        transparent
      );
    background-size: 200% 200%;
    animation: stars-drift 60s linear infinite;
  }
  @keyframes stars-drift {
    from {
      background-position: 0% 0%;
    }
    to {
      background-position: 100% 100%;
    }
  }
  .bg-nebula {
    background:
      radial-gradient(
        ellipse at 20% 80%,
        rgba(139, 92, 246, 0.15) 0%,
        transparent 50%
      ),
      radial-gradient(
        ellipse at 80% 20%,
        rgba(59, 130, 246, 0.12) 0%,
        transparent 50%
      );
    animation: nebula-pulse 15s ease-in-out infinite alternate;
  }
  @keyframes nebula-pulse {
    from {
      opacity: 0.6;
    }
    to {
      opacity: 1;
    }
  }
  .bg-vignette {
    background: radial-gradient(
      ellipse at center,
      transparent 0%,
      rgba(5, 5, 16, 0.4) 60%,
      rgba(5, 5, 16, 0.9) 100%
    );
  }

  /* Particles */
  .particles-container {
    position: absolute;
    inset: 0;
    pointer-events: none;
    overflow: hidden;
  }
  .particle {
    position: absolute;
    background: radial-gradient(
      circle,
      rgba(139, 92, 246, 0.8),
      transparent 70%
    );
    border-radius: 50%;
    animation: particle-float linear infinite;
  }
  @keyframes particle-float {
    0% {
      transform: translateY(100vh) scale(0);
      opacity: 0;
    }
    10% {
      opacity: 0.3;
      transform: translateY(80vh) scale(1);
    }
    90% {
      opacity: 0.3;
    }
    100% {
      transform: translateY(-20vh) scale(0.5);
      opacity: 0;
    }
  }
  .kanji-container {
    position: absolute;
    inset: 0;
    pointer-events: none;
    overflow: hidden;
  }
  .floating-kanji {
    position: absolute;
    bottom: -100px;
    font-size: 4rem;
    font-weight: 100;
    color: rgba(139, 92, 246, 0.06);
    animation: kanji-rise linear infinite;
  }
  @keyframes kanji-rise {
    0% {
      transform: translateY(0) rotate(0deg);
      opacity: 0;
    }
    5% {
      opacity: 0.06;
    }
    95% {
      opacity: 0.06;
    }
    100% {
      transform: translateY(-120vh) rotate(20deg);
      opacity: 0;
    }
  }

  /* Content */
  .content {
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 20px;
    max-width: 500px;
    width: 100%;
  }

  /* Title */
  .title-container {
    margin-bottom: 8px;
  }
  .game-title {
    font-size: clamp(3rem, 12vw, 5.5rem);
    font-weight: 900;
    letter-spacing: -0.03em;
    margin: 0;
    line-height: 1;
    text-shadow: 0 0 60px rgba(139, 92, 246, 0.5);
  }
  .title-lang {
    color: #e2e8f0;
  }
  .title-hero {
    background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 50%, #6366f1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .tagline {
    font-size: 1.2rem;
    font-weight: 600;
    color: #a78bfa;
    margin: 0 0 40px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
  }

  /* Menu Buttons */
  .menu-options {
    display: flex;
    flex-direction: column;
    gap: 10px;
    width: 100%;
  }
  .menu-btn {
    display: flex;
    align-items: center;
    gap: 14px;
    width: 100%;
    padding: 16px 18px;
    border: none;
    border-radius: 14px;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s ease;
    position: relative;
    touch-action: manipulation;
    -webkit-tap-highlight-color: transparent;
    min-height: 56px;
  }
  .menu-btn:active {
    transform: scale(0.98);
  }

  .menu-btn.primary {
    background: linear-gradient(
      135deg,
      rgba(139, 92, 246, 0.25),
      rgba(99, 102, 241, 0.25)
    );
    border: 1px solid rgba(139, 92, 246, 0.4);
  }
  .menu-btn.primary:hover {
    border-color: rgba(139, 92, 246, 0.6);
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.2);
  }

  .menu-btn.secondary {
    background: rgba(59, 130, 246, 0.12);
    border: 1px solid rgba(59, 130, 246, 0.25);
  }
  .menu-btn.secondary:hover {
    border-color: rgba(59, 130, 246, 0.45);
  }

  .menu-btn.tertiary {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
  }
  .menu-btn.tertiary:hover {
    border-color: rgba(255, 255, 255, 0.15);
  }

  .menu-btn.compact {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 10px 14px;
    min-height: 44px;
  }
  .menu-btn.compact:hover {
    border-color: rgba(255, 255, 255, 0.12);
  }
  .menu-btn.compact .btn-label {
    font-size: 0.9rem;
    color: #94a3b8;
  }
  .menu-btn.compact:hover .btn-label {
    color: #e2e8f0;
  }

  .btn-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    flex-shrink: 0;
  }
  .btn-icon svg {
    width: 20px;
    height: 20px;
    color: #cbd5e1;
  }
  .menu-btn.primary .btn-icon {
    background: rgba(139, 92, 246, 0.25);
  }
  .menu-btn.primary .btn-icon svg {
    color: #c4b5fd;
  }
  .btn-icon.small {
    width: 32px;
    height: 32px;
    background: rgba(255, 255, 255, 0.05);
  }
  .btn-icon.small svg {
    width: 16px;
    height: 16px;
    color: #64748b;
  }

  .btn-text {
    display: flex;
    flex-direction: column;
    gap: 2px;
    flex: 1;
  }
  .btn-label {
    font-size: 1rem;
    font-weight: 700;
    color: #f1f5f9;
  }
  .menu-btn.primary .btn-label {
    color: #fff;
  }
  .btn-subtitle {
    font-size: 0.8rem;
    font-weight: 500;
    color: #64748b;
  }
  .btn-arrow {
    font-size: 1.2rem;
    color: #8b5cf6;
  }

  .menu-divider {
    height: 1px;
    margin: 6px 0;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(255, 255, 255, 0.08),
      transparent
    );
  }

  /* Sub-views */
  .sub-view {
    width: 100%;
  }
  .back-btn {
    background: none;
    border: none;
    color: #8b5cf6;
    font-size: 0.95rem;
    font-weight: 600;
    cursor: pointer;
    padding: 8px 0;
    margin-bottom: 12px;
    text-align: left;
  }
  .back-btn:hover {
    color: #a78bfa;
  }
  .sub-title {
    font-size: 1.3rem;
    font-weight: 700;
    color: #f1f5f9;
    margin: 0 0 20px;
    text-align: left;
  }

  /* Story Cards */
  .card-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .story-card {
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    padding: 18px;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s ease;
    width: 100%;
  }
  .story-card:hover {
    border-color: rgba(139, 92, 246, 0.4);
    background: rgba(139, 92, 246, 0.08);
  }
  .story-card:active {
    transform: scale(0.98);
  }
  .story-card.disabled {
    opacity: 0.4;
    cursor: default;
  }
  .story-card.disabled:hover {
    border-color: rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.04);
  }

  .card-lang {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #8b5cf6;
  }
  .card-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #f1f5f9;
  }
  .card-desc {
    font-size: 0.9rem;
    color: #94a3b8;
    line-height: 1.4;
  }
  .card-meta {
    display: flex;
    gap: 12px;
    font-size: 0.8rem;
  }
  .card-state {
    color: #34d399;
    font-weight: 600;
    padding: 2px 8px;
    background: rgba(52, 211, 153, 0.1);
    border-radius: 6px;
  }
  .card-date {
    color: #64748b;
    padding: 2px 0;
  }
  .card-badge {
    font-size: 0.7rem;
    font-weight: 700;
    color: #c4b5fd;
    padding: 2px 8px;
    background: rgba(139, 92, 246, 0.15);
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .card-arrow {
    font-size: 0.9rem;
    font-weight: 600;
    color: #8b5cf6;
    margin-top: 4px;
  }

  .loading-text {
    color: #64748b;
    font-style: italic;
  }

  /* Footer */
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

  /* Mobile */
  @media (max-width: 700px) {
    .menu-btn {
      padding: 18px 20px;
      min-height: 64px;
    }
    .floating-kanji {
      font-size: 2.5rem;
    }
    .btn-subtitle {
      display: block;
    }
  }
  @media (prefers-reduced-motion: reduce) {
    .bg-stars,
    .bg-nebula,
    .particle,
    .floating-kanji {
      animation: none;
    }
    .menu-btn,
    .story-card {
      transition: none;
    }
  }
</style>
