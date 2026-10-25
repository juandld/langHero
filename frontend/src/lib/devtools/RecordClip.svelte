<script>
  import { getString, STORAGE_KEYS } from '$lib/utils/storage';

  export let isRecording = false;
  export let currentPanel = null;
  export let selectedOption = null;
  export let previewedOption = null;

  let devIsRecordingClip = false;
  let devClipRecorder = null;
  let devClipStream = null;
  let devClipChunks = [];
  let devClipDuration = 5;

  export function cleanup() {
    if (devClipRecorder && devClipRecorder.state !== 'inactive') {
      try { devClipRecorder.stop(); } catch (_) {}
    }
    if (devClipStream) {
      devClipStream.getTracks().forEach(t => t.stop());
    }
  }

  async function startDevClipRecording() {
    if (devIsRecordingClip || isRecording) return;
    try {
      const micId = getString(STORAGE_KEYS.MIC_DEVICE_ID, '');
      let stream;
      try {
        const audioConstraints = micId ? { deviceId: { exact: micId } } : true;
        stream = await navigator.mediaDevices.getUserMedia({ audio: audioConstraints });
      } catch (_) {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      devClipStream = stream;
      devClipChunks = [];
      const recorder = new MediaRecorder(stream);
      devClipRecorder = recorder;
      recorder.ondataavailable = (e) => { if (e.data) devClipChunks = [...devClipChunks, e.data]; };
      recorder.onstop = () => {
        const blob = new Blob(devClipChunks, { type: recorder.mimeType || 'audio/mp4' });
        const optTarget = selectedOption?.example?.target || previewedOption?.example?.target || 'clip';
        const safePanelId = (currentPanel?.id || 'unknown').replace(/[^a-zA-Z0-9_-]/g, '_');
        const safeTarget = optTarget.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 30);
        const ts = Date.now();
        const filename = `${safePanelId}_${safeTarget}_${ts}.webm`;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = filename; a.click();
        URL.revokeObjectURL(url);
        devClipStream?.getTracks().forEach(t => t.stop());
        devClipStream = null;
        devClipRecorder = null;
        devIsRecordingClip = false;
      };
      recorder.start(200);
      devIsRecordingClip = true;
      setTimeout(() => { if (devIsRecordingClip) stopDevClipRecording(); }, devClipDuration * 1000);
    } catch (err) {
      console.error('[DevClip] Mic error:', err);
    }
  }

  function stopDevClipRecording() {
    if (devClipRecorder && devClipRecorder.state !== 'inactive') {
      devClipRecorder.stop();
    }
  }
</script>

<div class="dev-separator"></div>
<div class="dev-title">Record Clip</div>
<div class="dev-row">
  <label class="dev-label" for="clip-duration">Duration (s)</label>
  <input id="clip-duration" type="number" class="dev-input-sm" min="1" max="30" bind:value={devClipDuration} />
</div>
<button
  class="dev-inject-btn"
  class:dev-recording={devIsRecordingClip}
  on:click={() => devIsRecordingClip ? stopDevClipRecording() : startDevClipRecording()}
  disabled={isRecording}
>
  {devIsRecordingClip ? 'Stop Recording' : 'Record'}
</button>

<style>
  .dev-separator {
    height: 1px;
    background: rgba(255, 255, 255, 0.08);
    margin: 6px 0;
  }

  .dev-title {
    font-size: 0.6rem;
    color: #52525b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
  }

  .dev-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 3px 0;
  }

  .dev-label {
    font-size: 0.65rem;
    color: #71717a;
    white-space: nowrap;
  }

  .dev-input-sm {
    width: 60px;
    padding: 2px 4px;
    font-size: 0.65rem;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 4px;
    color: #d4d4d8;
    text-align: center;
  }

  .dev-inject-btn {
    margin-top: 4px;
    width: 100%;
    padding: 4px 8px;
    font-size: 0.7rem;
    font-weight: 600;
    background: rgba(99, 102, 241, 0.25);
    border: 1px solid rgba(99, 102, 241, 0.4);
    border-radius: 5px;
    color: #a5b4fc;
    cursor: pointer;
    transition: background 0.15s;
  }

  .dev-inject-btn:hover:not(:disabled) {
    background: rgba(99, 102, 241, 0.4);
  }

  .dev-inject-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .dev-inject-btn.dev-recording {
    background: rgba(239, 68, 68, 0.35);
    border-color: rgba(239, 68, 68, 0.6);
    color: #fca5a5;
    animation: pulse-recording 1s ease-in-out infinite;
  }

  @keyframes pulse-recording {
    0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
    50% { box-shadow: 0 0 8px 2px rgba(239, 68, 68, 0.3); }
  }
</style>
