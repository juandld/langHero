<script lang="ts">
  import { onMount } from 'svelte';
  import { getApiBase } from '$lib/api';
  import {
    scoreToBand,
    scoreToPercent,
    bandColorHex,
    worstDimension,
    type Scores,
  } from '$lib/practice/scoring';

  type Turn = { role: 'tutor' | 'learner'; text: string };

  type ScenarioTurn = { role: 'tutor' | 'learner'; text: string; translation?: string };

  type Scenario = {
    id: string;
    title: string;
    description: string;
    target_language: string;
    register: string;
    starter_turns: ScenarioTurn[];
    learner_goal: string;
    success_criteria: string;
  };

  const DIMENSIONS: { key: keyof Scores; label: string }[] = [
    { key: 'grammatical', label: 'Grammar' },
    { key: 'natural', label: 'Natural' },
    { key: 'register', label: 'Register' },
    { key: 'meaning', label: 'Meaning' },
  ];

  let scenarios: Scenario[] = [];
  let selected: Scenario | null = null;

  let messages: Turn[] = [];
  let input = '';
  let sending = false;
  let scores: Scores = { grammatical: 0.7, natural: 0.7, register: 0.7, meaning: 0.7 };
  let alternative = '';
  let sessionId = '';
  let learnerLevel = 'A2';

  $: worst = worstDimension(scores);

  onMount(async () => {
    sessionId = crypto.randomUUID();
    try {
      learnerLevel = localStorage.getItem('LANGHERO_LEARNER_LEVEL') || 'A2';
    } catch {
      /* localStorage unavailable (SSR / privacy mode) — stays A2 default */
    }
    try {
      const res = await fetch(`${getApiBase()}/api/practice/scenarios`);
      scenarios = await res.json();
    } catch {
      scenarios = [];
    }
    // (intentional) do not auto-pick; let the user choose from the picker view.
  });

  function pick(scenario: Scenario) {
    selected = scenario;
    messages = scenario.starter_turns.map((t) => ({ role: t.role, text: t.text }));
  }

  async function send() {
    const text = input.trim();
    if (!text || sending || !selected) return;

    messages = [...messages, { role: 'learner', text }];
    input = '';
    sending = true;

    try {
      const res = await fetch(`${getApiBase()}/api/practice/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_language: selected.target_language,
          history: messages.map((m) => ({ role: m.role, text: m.text })),
          user_message: text,
          user_intent: text,
          scenario: `${selected.title} — ${selected.description} (${selected.register} register)`,
          learner_level: learnerLevel,
          session_id: sessionId,
        }),
      });
      const data = await res.json();
      messages = [...messages, { role: 'tutor', text: data.tutor_turn }];
      scores = data.scores;
      alternative = data.alternative || '';
    } finally {
      sending = false;
    }
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  $: pageTitle = selected ? `Practice: ${selected.title} · LangHero` : 'Practice · LangHero';
</script>

<svelte:head><title>{pageTitle}</title></svelte:head>

<div class="practice-page">
  <h1>Practice</h1>

  {#if !selected}
    <div data-testid="practice-scenario-menu" class="scenario-menu">
      <p class="scenario-menu-intro">Pick a scenario to start practicing:</p>
      {#each scenarios as scenario}
        <button
          data-testid="practice-scenario-{scenario.id}"
          class="scenario-card"
          on:click={() => pick(scenario)}
        >
          <span class="scenario-card-title">{scenario.title}</span>
          <span class="scenario-card-description">{scenario.description}</span>
        </button>
      {/each}
    </div>
  {:else}
    <p class="scenario">{selected.title} — {selected.description}</p>

    <div class="chat-list">
      {#each messages as msg}
        <div class="message {msg.role}">
          <span class="role">{msg.role === 'tutor' ? 'Tutor' : 'You'}</span>
          <span class="text">{msg.text}</span>
        </div>
      {/each}
    </div>

    <div data-testid="practice-feedback-bar" class="feedback-bar">
      {#each DIMENSIONS as dim}
        <div
          data-testid="practice-bar-{dim.key}"
          data-score={scores[dim.key].toFixed(2)}
          class="bar"
        >
          <span class="bar-label">{dim.label}</span>
          <div class="bar-track">
            <div
              class="bar-fill"
              style="width: {scoreToPercent(scores[dim.key])}%; background: {bandColorHex(
                scoreToBand(scores[dim.key]),
              )};"
            ></div>
          </div>
        </div>
      {/each}
    </div>

    {#if worst}
      <div class="alternative-callout">
        <strong>Try a more native phrasing:</strong>
        {#if alternative}
          <p>{alternative}</p>
        {:else}
          <p>Keep going — the tutor will suggest a native alternative after your next turn.</p>
        {/if}
      </div>
    {/if}

    <form class="composer" on:submit|preventDefault={send}>
      <textarea
        data-testid="practice-chat-input"
        bind:value={input}
        on:keydown={onKeydown}
        placeholder="Type your response..."
        rows="2"
      ></textarea>
      <button data-testid="practice-chat-send" type="submit" disabled={sending || !input.trim()}>
        Send
      </button>
    </form>
  {/if}
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    background: #0f172a;
  }

  .practice-page {
    max-width: 640px;
    margin: 0 auto;
    padding: 24px 16px 40px;
    color: #e2e8f0;
    font-family: system-ui, sans-serif;
  }

  h1 {
    margin: 0 0 4px;
  }

  .scenario {
    color: #94a3b8;
    margin: 0 0 20px;
    font-style: italic;
  }

  .scenario-menu {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .scenario-menu-intro {
    color: #94a3b8;
    margin: 0 0 4px;
  }

  .scenario-card {
    display: flex;
    flex-direction: column;
    gap: 4px;
    text-align: left;
    padding: 14px 16px;
    border-radius: 10px;
    border: 1px solid #334155;
    background: #1e293b;
    color: #e2e8f0;
    cursor: pointer;
    font-family: inherit;
  }

  .scenario-card:hover {
    border-color: #2563eb;
  }

  .scenario-card-title {
    font-weight: 600;
  }

  .scenario-card-description {
    font-size: 13px;
    color: #94a3b8;
  }

  .chat-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-height: 120px;
    margin-bottom: 16px;
  }

  .message {
    padding: 10px 14px;
    border-radius: 10px;
    max-width: 80%;
  }

  .message.learner {
    align-self: flex-end;
    background: #2563eb;
  }

  .message.tutor {
    align-self: flex-start;
    background: #1e293b;
  }

  .role {
    display: block;
    font-size: 11px;
    opacity: 0.7;
    margin-bottom: 2px;
  }

  .feedback-bar {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: #1e293b;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 16px;
  }

  .bar {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .bar-label {
    width: 80px;
    font-size: 13px;
    color: #94a3b8;
  }

  .bar-track {
    flex: 1;
    height: 10px;
    background: #334155;
    border-radius: 6px;
    overflow: hidden;
  }

  .bar-fill {
    height: 100%;
    transition: width 0.3s ease;
  }

  .alternative-callout {
    background: #422006;
    border: 1px solid #eab308;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 16px;
    font-size: 14px;
  }

  .alternative-callout strong {
    color: #eab308;
  }

  .composer {
    display: flex;
    gap: 8px;
  }

  textarea {
    flex: 1;
    resize: none;
    border-radius: 8px;
    border: 1px solid #334155;
    background: #1e293b;
    color: #e2e8f0;
    padding: 10px;
    font-family: inherit;
    font-size: 14px;
  }

  button {
    padding: 0 20px;
    border-radius: 8px;
    border: none;
    background: #2563eb;
    color: white;
    font-weight: 600;
    cursor: pointer;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
