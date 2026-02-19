// Branch logic — pure functions for the branching/category system

export const RESPONSE_CATEGORIES = {
  diplomatic:       { label: 'Diplomatic',       color: '#86efac', icon: '🕊' },
  pragmatic:        { label: 'Pragmatic',        color: '#93c5fd', icon: '⚖' },
  bold:             { label: 'Bold',             color: '#fdba74', icon: '⚡' },
  hostile:          { label: 'Hostile',          color: '#fca5a5', icon: '🔥' },
  'history-breaking': { label: 'History-Breaking', color: '#e9d5ff', icon: '✦' },
};

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

export function getOptionCategory(option) {
  const style = option?.style || '';
  const key = STYLE_TO_CATEGORY[style] || 'pragmatic';
  return RESPONSE_CATEGORIES[key];
}

export function getCategoryKey(option) {
  const style = option?.style || '';
  return STYLE_TO_CATEGORY[style] || 'pragmatic';
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
