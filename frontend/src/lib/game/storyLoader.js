/**
 * Story Loader — manages lazy segment loading for anchor-based stories.
 *
 * Loads the skeleton on mount, then fetches segments on-demand as
 * the player progresses through anchors. Supports prefetching.
 */

import { getApiBase } from '$lib/api';

function getBase() { return getApiBase(); }

export function createStoryLoader(storyId) {
  let skeleton = null;
  let segmentCache = new Map(); // key: "fromAnchor->toAnchor" => panels[]
  let loading = false;

  /**
   * Load the story skeleton (lightweight anchor metadata).
   */
  async function loadSkeleton() {
    const res = await fetch(`${getBase()}/api/story-panels/stories/${storyId}/skeleton`);
    if (!res.ok) throw new Error(`Failed to load skeleton: ${res.status}`);
    skeleton = await res.json();
    return skeleton;
  }

  /**
   * Get the skeleton (must call loadSkeleton first).
   */
  function getSkeleton() {
    return skeleton;
  }

  /**
   * Load a segment's panels between two anchors.
   * Returns cached panels if available.
   */
  async function loadSegment(fromAnchorId, toAnchorId, playerState) {
    const cacheKey = `${fromAnchorId}->${toAnchorId}`;

    // Check local cache
    if (segmentCache.has(cacheKey)) {
      return { panels: segmentCache.get(cacheKey), cached: true, generated: false };
    }

    loading = true;
    try {
      const res = await fetch(`${getBase()}/api/story-panels/stories/${storyId}/segment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          from_anchor_id: fromAnchorId,
          to_anchor_id: toAnchorId,
          player_state: playerState || {},
        }),
      });

      if (!res.ok) throw new Error(`Failed to load segment: ${res.status}`);
      const data = await res.json();

      // Cache locally
      if (data.panels?.length > 0) {
        segmentCache.set(cacheKey, data.panels);
      }

      return data;
    } finally {
      loading = false;
    }
  }

  /**
   * Fire-and-forget prefetch for the next segment.
   */
  function prefetchNext(currentAnchorId, playerState) {
    if (!skeleton) return;

    // Find current anchor and its next
    const anchors = skeleton.anchors;
    const idx = anchors.findIndex(a => a.id === currentAnchorId);
    if (idx < 0 || idx + 1 >= anchors.length) return;

    const nextAnchor = anchors[idx + 1];
    const afterNext = idx + 2 < anchors.length ? anchors[idx + 2] : null;

    if (!afterNext) return;

    const cacheKey = `${nextAnchor.id}->${afterNext.id}`;
    if (segmentCache.has(cacheKey)) return; // Already cached

    // Fire and forget
    fetch(`${getBase()}/api/story-panels/stories/${storyId}/prefetch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        from_anchor_id: nextAnchor.id,
        to_anchor_id: afterNext.id,
        player_state: playerState || {},
      }),
    }).catch(() => {}); // Silently ignore prefetch failures
  }

  /**
   * Get the anchor after the given one (respecting next_anchor overrides).
   */
  function getNextAnchor(anchorId) {
    if (!skeleton) return null;
    const anchors = skeleton.anchors;
    const anchor = anchors.find(a => a.id === anchorId);

    if (!anchor) return null;

    // Explicit next_anchor override
    if (anchor.next_anchor) {
      return anchors.find(a => a.id === anchor.next_anchor) || null;
    }

    // Sequential
    const idx = anchors.findIndex(a => a.id === anchorId);
    if (idx < 0 || idx + 1 >= anchors.length) return null;
    return anchors[idx + 1];
  }

  /**
   * Get the chapter for an anchor ID.
   */
  function getChapterForAnchor(anchorId) {
    if (!skeleton) return null;
    const anchor = skeleton.anchors.find(a => a.id === anchorId);
    if (!anchor) return null;
    return skeleton.chapters.find(ch => ch.anchor_ids.includes(anchorId));
  }

  /**
   * Get all anchor IDs in order.
   */
  function getAnchorIds() {
    if (!skeleton) return [];
    return skeleton.anchors.map(a => a.id);
  }

  /**
   * Resolve a reputation gate — returns the target anchor ID.
   */
  function resolveGate(anchorId, reputation) {
    if (!skeleton) return null;
    const anchor = skeleton.anchors.find(a => a.id === anchorId);
    if (!anchor || anchor.type !== 'reputation_gate' || !anchor.gate_config) return null;

    const { category, threshold, pass_anchor, fail_anchor } = anchor.gate_config;

    // Special case: empty category means "use dominant category"
    if (!category) {
      // Find dominant reputation category
      let maxCat = 'pragmatic';
      let maxVal = -1;
      for (const [cat, val] of Object.entries(reputation || {})) {
        if (val > maxVal) { maxVal = val; maxCat = cat; }
      }
      // G3: always passes, ending logic uses dominant category
      return pass_anchor;
    }

    const value = reputation[category] || 0;
    return value >= threshold ? pass_anchor : fail_anchor;
  }

  /**
   * Get the dominant reputation category.
   */
  function getDominantCategory(reputation) {
    let maxCat = 'pragmatic';
    let maxVal = -1;
    for (const [cat, val] of Object.entries(reputation || {})) {
      if (val > maxVal) { maxVal = val; maxCat = cat; }
    }
    return maxCat;
  }

  return {
    loadSkeleton,
    getSkeleton,
    loadSegment,
    prefetchNext,
    getNextAnchor,
    getChapterForAnchor,
    getAnchorIds,
    resolveGate,
    getDominantCategory,
    get loading() { return loading; },
    get skeleton() { return skeleton; },
  };
}
