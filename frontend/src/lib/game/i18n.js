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
  // speak loop + assistant (were hardcoded Spanish in Nellie's Manuela work; shared by every story)
  release_speak: { en: 'Release Time & Speak', es: 'Soltar el tiempo y hablar' },
  stop_send: { en: 'Stop & Submit', es: 'Detener y enviar' },
  speak: { en: 'Speak', es: 'Hablar' },
  stop_speaking: { en: 'Stop Speaking', es: 'Dejar de hablar' },
  recording: { en: '🎙️ Recording…', es: '🎙️ Grabando…' },
  processing_audio: { en: '⏳ Processing audio…', es: '⏳ Procesando audio…' },
  speak_now_hint: { en: 'Speak now — tap the button again to send', es: 'Habla ahora — pulsa el botón otra vez para enviar' },
  sending_audio: { en: 'Sending audio to the server…', es: 'Enviando audio al servidor…' },
  no_server_response: { en: 'No response from the server — try again', es: 'Sin respuesta del servidor — intenta otra vez' },
  recording_too_short: { en: 'Recording too short — try again', es: 'Grabación muy corta — intenta otra vez' },
  recording_error: { en: 'Recording error — try again', es: 'Error al grabar — intenta otra vez' },
  send_error: { en: 'Could not send — try again', es: 'Error al enviar — intenta otra vez' },
  mic_denied: { en: 'Microphone access denied. Allow it in your browser settings.', es: 'Acceso al micrófono denegado. Permítelo en los ajustes del navegador.' },
  mic_unavailable: { en: 'Could not access the microphone', es: 'No se pudo acceder al micrófono' },
  voice_unsupported: { en: 'Voice recording is not available in this browser', es: 'Grabación de voz no disponible en este navegador' },
  listening_now: { en: 'Listening... speak now!', es: 'Escuchando... ¡Habla ahora!' },
  tap_to_speak: { en: 'Tap to speak', es: 'Toca para hablar' },
  good_try: { en: 'Good try!', es: '¡Buen intento!' },
  perfect: { en: 'Perfect!', es: '¡Perfecto!' },
  out_of_lives: { en: "You're out of lives. Try another option.", es: 'Se te acabaron las vidas. Prueba otra opción.' },
  heard: { en: 'Heard:', es: 'Oí:' },
  assistant_title: { en: 'Time guide', es: 'Guía del tiempo' },
  connection_error: { en: 'Connection error — try again', es: 'Error de conexión — intenta otra vez' },
};

/**
 * UI chrome language for a story: the learner's narration-language setting wins; otherwise a story can
 * declare `ui_lang` (Manuela is Spanish-immersion); otherwise English.
 * @param {string} [narrationLanguage]
 * @param {any} [story]
 */
export function uiLangFor(narrationLanguage, story) {
  return narrationLanguage || (story && story.ui_lang) || '';
}

/**
 * @param {string} key
 * @param {string} [lang]
 */
export function t(key, lang) {
  const entry = /** @type {Record<string, {en: string, es: string}>} */ (STRINGS)[key];
  if (!entry) return key;
  return entry[/** @type {'en'|'es'} */ (lang)] || entry.en;
}
