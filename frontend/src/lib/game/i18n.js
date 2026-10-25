// Minimal UI-chrome translations. Story/narration text is already localized
// server-side (backend/story/localize.py + localize_cache); this covers the
// client-rendered labels/buttons around it that were always hardcoded
// English regardless of the narration-language setting (GameMenu's "Story
// narration" dropdown, STORAGE_KEYS.NARRATION_LANGUAGE — '' or 'es').
const STRINGS = {
  time_stopped: { en: 'TIME STOPPED - How will you respond?', es: 'TIEMPO DETENIDO - ¿Cómo vas a responder?' },
  draft_placeholder: { en: 'Tell Bimbo what you want to say...', es: 'Dile a Bimbo lo que quieres decir...' },
  ask: { en: 'Ask', es: 'Preguntar' },
  bimbo_label: { en: 'Bimbo:', es: 'Bimbo:' },
  suggestions_label: { en: 'Suggestions — tap to hear', es: 'Sugerencias — toca para escuchar' },
  speak_freely: { en: 'Speak freely in the target language', es: 'Habla libremente en el idioma objetivo' },
  you_said: { en: 'You said:', es: 'Dijiste:' },
  continue: { en: 'Continue →', es: 'Continuar →' },
  skip: { en: 'Skip →', es: 'Saltar →' },
  loading_story: { en: 'Loading story...', es: 'Cargando historia...' },
  back: { en: '← Back', es: '← Atrás' },
  next: { en: 'Next →', es: 'Siguiente →' },
  finish: { en: 'Finish', es: 'Terminar' },
};

/**
 * @param {string} key
 * @param {string} [lang]
 */
export function t(key, lang) {
  const entry = /** @type {Record<string, {en: string, es: string}>} */ (STRINGS)[key];
  if (!entry) return key;
  return entry[/** @type {'en'|'es'} */ (lang)] || entry.en;
}
