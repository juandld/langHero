/**
 * Timeline recorder — the time-correlated observability layer for audio sync.
 *
 * Attaches `window.__langheroTimeline` on page load. Captures:
 *  - every <audio> element's play / pause / ended / timeupdate (throttled)
 *  - navigations (route changes pushed by callers via push('panel_entered', ...))
 *  - fetch starts/finishes for /api/* calls
 *
 * Downstream: `/api/observability/timeline/{session_id}` ingests batches,
 * `/observability/timeline/{session_id}` renders a Gantt-strip. This module
 * only records; the backend and UI slice land in a follow-up tick.
 *
 * Design: idempotent attach, memory-capped at MAX_EVENTS, zero-cost on SSR.
 */

export type TimelineEvent = {
  t_ms: number;         // monotonic ms since recorder start
  kind: string;         // "audio_play" | "audio_pause" | "audio_ended" | "audio_timeupdate" | "panel_entered" | "fetch_start" | "fetch_end" | ...
  data?: unknown;
};

export type TimelineAPI = {
  sessionId: string;
  startedAt: number;    // epoch ms
  events: TimelineEvent[];
  push: (kind: string, data?: unknown) => void;
  getAll: () => TimelineEvent[];
  clear: () => void;
  stats: () => Record<string, number>;
  flush: () => Promise<void>;  // POST unsent events to backend
};

declare global {
  interface Window {
    __langheroTimeline?: TimelineAPI;
  }
}

const MAX_EVENTS = 2000;
const AUDIO_SAMPLE_MS = 250;
const FLUSH_INTERVAL_MS = 15000;
const BACKEND_BASE = (import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env?.VITE_API_BASE || '';
function resolveBackend(): string {
  if (BACKEND_BASE) return BACKEND_BASE;
  if (typeof window !== 'undefined') {
    // Dev proxy: frontend 5200 → backend 8100 (same host, swap port).
    const u = new URL(window.location.href);
    if (u.port === '5200') return `http://${u.hostname}:8100`;
    return u.origin;
  }
  return '';
}

function makeSessionId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return `tl-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

export function attachTimeline(): TimelineAPI | null {
  if (typeof window === 'undefined') return null;
  if (window.__langheroTimeline) return window.__langheroTimeline;

  const startedAt = Date.now();
  const events: TimelineEvent[] = [];
  let lastFlushedIndex = 0;
  const sessionId = makeSessionId();
  const backend = resolveBackend();

  const api: TimelineAPI = {
    sessionId,
    startedAt,
    events,
    push(kind, data) {
      events.push({ t_ms: Date.now() - startedAt, kind, data });
      if (events.length > MAX_EVENTS) {
        const dropped = events.length - MAX_EVENTS;
        events.splice(0, dropped);
        lastFlushedIndex = Math.max(0, lastFlushedIndex - dropped);
      }
    },
    getAll() { return events.slice(); },
    clear() { events.length = 0; lastFlushedIndex = 0; },
    stats() {
      const by: Record<string, number> = {};
      for (const e of events) by[e.kind] = (by[e.kind] || 0) + 1;
      return by;
    },
    async flush(viaUnload = false) {
      if (lastFlushedIndex >= events.length) return;
      const batch = events.slice(lastFlushedIndex);
      const sendIndex = events.length;
      // keepalive: true has a 64KB per-request limit and silently drops larger
      // bodies — fine for the small shutdown batch (beforeunload / pagehide),
      // not for the 15s periodic flush which can carry hundreds of events.
      try {
        const r = await window.fetch(`${backend}/api/observability/timeline/${sessionId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ events: batch }),
          keepalive: viaUnload,
        });
        if (r.ok) lastFlushedIndex = sendIndex;
      } catch { /* swallow — flushes are best-effort */ }
    },
  };

  window.__langheroTimeline = api;

  // Hook every <audio> element — current ones + any added later.
  const lastSampleAt = new WeakMap<HTMLAudioElement, number>();
  const hookAudio = (el: HTMLAudioElement) => {
    if ((el as unknown as { __tlHooked?: boolean }).__tlHooked) return;
    (el as unknown as { __tlHooked: boolean }).__tlHooked = true;
    el.addEventListener('play',  () => api.push('audio_play',  { src: el.currentSrc, currentTime: el.currentTime }));
    el.addEventListener('pause', () => api.push('audio_pause', { src: el.currentSrc, currentTime: el.currentTime }));
    el.addEventListener('ended', () => api.push('audio_ended', { src: el.currentSrc, currentTime: el.currentTime }));
    el.addEventListener('timeupdate', () => {
      const now = Date.now();
      const prev = lastSampleAt.get(el) ?? 0;
      if (now - prev < AUDIO_SAMPLE_MS) return;
      lastSampleAt.set(el, now);
      api.push('audio_timeupdate', { currentTime: el.currentTime });
    });
  };

  document.querySelectorAll('audio').forEach((el) => hookAudio(el as HTMLAudioElement));
  const mo = new MutationObserver((muts) => {
    for (const m of muts) {
      m.addedNodes.forEach((n) => {
        if (n instanceof HTMLAudioElement) hookAudio(n);
        else if (n instanceof HTMLElement) {
          n.querySelectorAll?.('audio').forEach((el) => hookAudio(el as HTMLAudioElement));
        }
      });
    }
  });
  mo.observe(document.body, { childList: true, subtree: true });

  // The game creates audio via `new Audio(src)` in 6 call sites (audioStore,
  // api.ts, DialogueOverlay, FirstChallenge, AwakeningCutscene, audioEngine)
  // — none are appended to the DOM, so the MutationObserver above misses them.
  // Wrap the constructor so every programmatic instance gets hooked at birth.
  const OrigAudio = window.Audio;
  const HookedAudio = function (src?: string) {
    const el = src !== undefined ? new OrigAudio(src) : new OrigAudio();
    hookAudio(el);
    return el;
  } as unknown as typeof window.Audio;
  HookedAudio.prototype = OrigAudio.prototype;
  // Preserve static props (there aren't typically any, but defensive)
  Object.setPrototypeOf(HookedAudio, OrigAudio);
  window.Audio = HookedAudio;

  // Hook history navigation so every route change emits a panel_entered event.
  // Gives sync-stats a correlation anchor independent of fetch_start — useful
  // when audio is cached locally and no network request precedes playback.
  const emitPanel = () => {
    api.push('panel_entered', { path: window.location.pathname, href: window.location.href });
  };
  const origPushState = history.pushState.bind(history);
  const origReplaceState = history.replaceState.bind(history);
  history.pushState = function (data: unknown, unused: string, url?: string | URL | null) {
    const r = origPushState(data, unused, url ?? null);
    setTimeout(emitPanel, 0);
    return r;
  };
  history.replaceState = function (data: unknown, unused: string, url?: string | URL | null) {
    const r = origReplaceState(data, unused, url ?? null);
    setTimeout(emitPanel, 0);
    return r;
  };
  window.addEventListener('popstate', emitPanel);
  emitPanel(); // seed with the initial route

  // Hook fetch for /api/* calls so we can correlate network with audio.
  // Exclude the observability ingest endpoint so flush() calls don't record
  // themselves — otherwise each flush pushes 2 fetch_* events that trigger
  // the next flush, generating permanent 2-events-per-interval noise even
  // on a tab with zero real activity.
  const origFetch = window.fetch;
  window.fetch = async function patchedFetch(input: RequestInfo | URL, init?: RequestInit) {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.toString() : input.url;
    const isApi = /\/api\//.test(url) && !/\/api\/observability\/timeline\//.test(url);
    const started = Date.now() - startedAt;
    if (isApi) api.push('fetch_start', { url, method: init?.method || 'GET' });
    try {
      const r = await origFetch(input as RequestInfo, init);
      if (isApi) api.push('fetch_end', { url, status: r.status, dur_ms: (Date.now() - startedAt) - started });
      return r;
    } catch (e) {
      if (isApi) api.push('fetch_error', { url, err: String(e), dur_ms: (Date.now() - startedAt) - started });
      throw e;
    }
  };

  api.push('recorder_attached', { ua: navigator.userAgent.slice(0, 80) });

  // Periodic flush uses standard fetch (unlimited body); unload flushes use
  // keepalive so the browser can finish the request after the tab closes.
  setInterval(() => { api.flush(false); }, FLUSH_INTERVAL_MS);
  window.addEventListener('beforeunload', () => { api.flush(true); });
  window.addEventListener('pagehide', () => { api.flush(true); });

  return api;
}
