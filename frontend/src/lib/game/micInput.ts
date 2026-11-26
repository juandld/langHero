import { STORAGE_KEYS } from '$lib/utils';

/* ── Mic choice ── */
export function saveMicChoice(deviceId: string) {
  try {
    const id = String(deviceId || '').trim();
    if (!id) localStorage.removeItem(STORAGE_KEYS.MIC_DEVICE_ID);
    else localStorage.setItem(STORAGE_KEYS.MIC_DEVICE_ID, id);
  } catch (_) {}
}

/* ── Demo transcript ──
   The free demo (/demo) must not pay for transcription: the browser's own speech recognition
   supplies the transcript and the DEMO_MODE backend matches it locally. */
const SPEECH_LANG_CODES: Record<string, string> = {
  japanese: 'ja-JP', ja: 'ja-JP', mandarin: 'zh-CN', chinese: 'zh-CN', zh: 'zh-CN',
  spanish: 'es-ES', es: 'es-ES', english: 'en-US', en: 'en-US'
};

let recognizer: { stop: () => Promise<string> } | null = null;

export function startDemoRecognition(lang: string) {
  recognizer = null;
  const w = (typeof window !== 'undefined' ? window : {}) as any;
  const SR = w.SpeechRecognition || w.webkitSpeechRecognition;
  if (!SR) return;
  let text = '';
  const rec = new SR();
  rec.lang = SPEECH_LANG_CODES[String(lang || '').toLowerCase()] || 'ja-JP';
  rec.continuous = true;
  rec.interimResults = false;
  const ended = new Promise<string>((resolve) => {
    rec.onresult = (e: any) => { text = Array.from(e.results).map((r: any) => r[0]?.transcript || '').join(' ').trim(); };
    rec.onerror = () => {};
    rec.onend = () => resolve(text);
  });
  try { rec.start(); } catch (_) { return; }
  recognizer = {
    stop: () => {
      try { rec.stop(); } catch (_) {}
      return Promise.race([ended, new Promise<string>((r) => setTimeout(() => r(text), 1500))]);
    }
  };
}

/** Adds the demo transcript, if one was recorded, to the turn's upload. */
export async function appendDemoTranscript(formData: FormData) {
  if (!recognizer) return;
  const heard = await recognizer.stop();
  recognizer = null;
  if (heard) formData.append('transcript', heard);
}
