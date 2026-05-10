// Branch logic — pure functions for the branching/category system

// Default categories (used when no skeleton is loaded)
export const RESPONSE_CATEGORIES = {
  diplomatic:       { label: 'Diplomatic',       color: '#86efac', icon: '🕊' },
  pragmatic:        { label: 'Pragmatic',        color: '#93c5fd', icon: '⚖' },
  bold:             { label: 'Bold',             color: '#fdba74', icon: '⚡' },
  hostile:          { label: 'Hostile',          color: '#fca5a5', icon: '🔥' },
  'history-breaking': { label: 'History-Breaking', color: '#e9d5ff', icon: '✦' },
};

// Default style-to-category mapping
export const STYLE_TO_CATEGORY = {
  polite:      'diplomatic',
  charming:    'diplomatic',
  humble:      'diplomatic',
  friendly:    'diplomatic',

  cautious:    'pragmatic',
  honest:      'pragmatic',
  safe:        'pragmatic',
  vague:       'pragmatic',
  silent:      'pragmatic',
  obedient:    'pragmatic',
  curious:     'pragmatic',

  direct:      'bold',
  bold:        'bold',
  desperate:   'bold',

  hostile:     'hostile',
  defiant:     'hostile',
  threatening: 'hostile',

  insightful:  'history-breaking',
};

/**
 * Build categories and style mapping from a skeleton, falling back to defaults.
 */
export function buildCategoriesFromSkeleton(skeleton) {
  if (!skeleton) return { categories: RESPONSE_CATEGORIES, styleToCategory: STYLE_TO_CATEGORY };

  const categories = {};
  if (skeleton.categories) {
    for (const cat of skeleton.categories) {
      categories[cat.key] = { label: cat.label, color: cat.color, icon: cat.icon, description: cat.description };
    }
  }

  const styleToCategory = skeleton.style_to_category || STYLE_TO_CATEGORY;

  return {
    categories: Object.keys(categories).length > 0 ? categories : RESPONSE_CATEGORIES,
    styleToCategory,
  };
}

// Active categories (can be overridden per-story)
let _activeCategories = RESPONSE_CATEGORIES;
let _activeStyleMap = STYLE_TO_CATEGORY;

export function setActiveCategories(categories, styleToCategory) {
  _activeCategories = categories || RESPONSE_CATEGORIES;
  _activeStyleMap = styleToCategory || STYLE_TO_CATEGORY;
}

export function getOptionCategory(option) {
  const style = option?.style || '';
  const key = _activeStyleMap[style] || 'pragmatic';
  return _activeCategories[key];
}

export function getCategoryKey(option) {
  const style = option?.style || '';
  return _activeStyleMap[style] || 'pragmatic';
}

export function resolveBranch(panel, matchedIndex, category) {
  if (!panel) return null;
  // 1. Matched option has explicit outcome.next_panel
  if (matchedIndex >= 0 && panel.options?.[matchedIndex]?.outcome?.next_panel) {
    return panel.options[matchedIndex].outcome;
  }
  // 2. Panel has category_outcomes for this category
  if (panel.category_outcomes?.[category]) {
    return panel.category_outcomes[category];
  }
  // 3. Panel has default_outcome
  if (panel.default_outcome) {
    return panel.default_outcome;
  }
  // 4. Not a branch_point — sequential advance
  return null;
}

export function resolvePanel(panel, playerChoices, branchHist) {
  if (!panel || !panel.choice_variants) return panel;
  for (const [sourcePanelId, optionMap] of Object.entries(panel.choice_variants)) {
    // Check branchHistory for category-keyed variants first
    const branchEntry = branchHist?.find(b => b.panelId === sourcePanelId);
    if (branchEntry && optionMap[branchEntry.category]) {
      return { ...panel, ...optionMap[branchEntry.category] };
    }
    // Fall back to integer option index
    const chosenIndex = playerChoices[sourcePanelId];
    if (chosenIndex !== undefined && optionMap[String(chosenIndex)]) {
      const variant = optionMap[String(chosenIndex)];
      return { ...panel, ...variant };
    }
  }
  return panel;
}

/**
 * Find a panel by ID across all chapters.
 * @returns {{ chapterIndex: number, panelIndex: number } | null}
 */
export function findPanelLocation(story, panelId) {
  if (!story?.chapters) return null;
  for (let ci = 0; ci < story.chapters.length; ci++) {
    const ch = story.chapters[ci];
    for (let pi = 0; pi < ch.panels.length; pi++) {
      if (ch.panels[pi].id === panelId) {
        return { chapterIndex: ci, panelIndex: pi };
      }
    }
  }
  return null;
}

/**
 * Get the chapter ID for a given anchor from the skeleton.
 */
export function getChapterForAnchorId(skeleton, anchorId) {
  if (!skeleton?.chapters) return null;
  for (const ch of skeleton.chapters) {
    if (ch.anchor_ids?.includes(anchorId)) return ch.id;
  }
  return null;
}
