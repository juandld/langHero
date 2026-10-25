<script>
  import { getOptionCategory } from '$lib/game/branchLogic';

  export let currentPanel = null;

  let devLastResult = null;
  let devLastLang = '';
  let devMatchThreshold = 0.7;
  let devMicLevel = 0;        // raw RMS of time-domain samples (0..~0.3 for speech)
  let devMicPeak = 0;         // highest level seen this session
  let devMicCtxState = '';    // 'running' | 'suspended' | 'closed'
  let devMicFirstFrame = null; // first-frame max deviation; null until measured

  export function setDevLastResult(r) { devLastResult = r; }
  export function setDevLastLang(l) { devLastLang = l; }
  export function setDevMicLevel(level) {
    devMicLevel = level;
    if (level > devMicPeak) devMicPeak = level;
  }
  export function setDevMicCtxState(state) { devMicCtxState = state; }
  export function setDevMicFirstFrame(dev) { devMicFirstFrame = dev; }
  export function resetDevMic() { devMicLevel = 0; devMicPeak = 0; devMicFirstFrame = null; }
</script>

<div class="dev-separator"></div>
<div class="dev-title">Mic Diagnostics</div>
<div class="dev-result-grid">
  <span class="dev-result-key">level</span>
  <span class="dev-result-val" style="color: {devMicLevel > 0.02 ? '#86efac' : devMicLevel > 0 ? '#fde047' : '#fca5a5'}">
    {(devMicLevel * 100).toFixed(0)}
  </span>
  <span class="dev-result-key">peak</span>
  <span class="dev-result-val">{(devMicPeak * 100).toFixed(0)}</span>
  <span class="dev-result-key">ctx</span>
  <span class="dev-result-val" style="color: {devMicCtxState === 'running' ? '#86efac' : devMicCtxState ? '#fca5a5' : '#64748b'}">
    {devMicCtxState || '—'}
  </span>
  <span class="dev-result-key">1st frame</span>
  <span class="dev-result-val">{devMicFirstFrame !== null ? devMicFirstFrame : '—'}</span>
</div>
<div class="dev-note">
  level/peak = RMS × 100 (0 = silence, 20+ = speaking). ctx = AudioContext state after resume. 1st frame = max deviation from 128 right after wiring (0 = dead pipeline).
</div>

<div class="dev-separator"></div>
<div class="dev-title">Match Threshold</div>
<div class="dev-row">
  <input type="range" class="dev-slider" min="0" max="1" step="0.05" bind:value={devMatchThreshold} />
  <span class="dev-value">{Math.round(devMatchThreshold * 100)}%</span>
</div>
<div class="dev-note">Frontend only. Backend uses 0.70.</div>

<div class="dev-separator"></div>
<div class="dev-title">Last Result</div>
{#if devLastResult}
  {@const matchedIdx = devLastResult.matched_index}
  {@const matchedOpt = (matchedIdx !== undefined && matchedIdx >= 0 && currentPanel?.options) ? currentPanel.options[matchedIdx] : null}
  {@const cat = getOptionCategory(matchedOpt)}
  <div class="dev-category-badge" style="background: {cat.color}20; border-color: {cat.color}40; color: {cat.color}">
    {cat.icon} {cat.label}
  </div>
  <div class="dev-result-grid">
    <span class="dev-result-key">tier</span>
    <span class="dev-result-val" style="color: {devLastResult.tier === 'perfect' ? '#86efac' : devLastResult.tier === 'good' ? '#86efac' : devLastResult.tier === 'passable' ? '#fbbf24' : devLastResult.tier === 'fumble' ? '#fdba74' : '#fca5a5'}">
      {devLastResult.tier || '—'}
    </span>
    <span class="dev-result-key">style</span>
    <span class="dev-result-val">{matchedOpt?.style || '—'}</span>
    <span class="dev-result-key">match</span>
    <span class="dev-result-val" style="color: {(devLastResult.match_level ?? 0) >= 0.9 ? '#86efac' : (devLastResult.match_level ?? 0) >= 0.7 ? '#fde047' : '#fca5a5'}">
      {Math.round((devLastResult.match_level ?? 0) * 100)}%
    </span>
    <span class="dev-result-key">heard</span>
    <span class="dev-result-val">{devLastResult.heard || '—'}</span>
    <span class="dev-result-key">expected</span>
    <span class="dev-result-val">{devLastResult.expected || devLastResult.expected_response || '—'}</span>
    <span class="dev-result-key">lang</span>
    <span class="dev-result-val">{devLastResult.detected_language || '—'}</span>
  </div>
{:else}
  <div class="dev-note">No result yet</div>
{/if}

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

  .dev-slider {
    flex: 1;
    height: 4px;
    accent-color: #6366f1;
    cursor: pointer;
  }

  .dev-value {
    font-size: 0.7rem;
    color: #a5b4fc;
    font-weight: 600;
    min-width: 32px;
    text-align: right;
  }

  .dev-note {
    font-size: 0.55rem;
    color: #52525b;
    font-style: italic;
    margin-top: 2px;
  }

  .dev-category-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    border: 1px solid;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 600;
    margin-bottom: 4px;
  }

  .dev-result-grid {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: 2px 8px;
    font-size: 0.65rem;
  }

  .dev-result-key {
    color: #52525b;
    text-align: right;
  }

  .dev-result-val {
    color: #a1a1aa;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
</style>
