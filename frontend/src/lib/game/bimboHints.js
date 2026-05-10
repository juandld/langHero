/**
 * Bimbo Hints — reputation-based personality comments.
 *
 * At certain moments during gameplay, Bimbo makes subtle comments
 * about the player's dominant personality. Triggered when the
 * dominant category shifts or reputation delta >= 2 since last hint.
 */

const HINT_POOL = {
  diplomatic: [
    "You've been quite the diplomat lately... choosing your words like a silk merchant choosing threads.",
    "Careful words, careful steps. You remind me of the court advisors back home.",
    "Always the peacemaker. There's strength in that, you know.",
    "Words as smooth as sake. The lords are starting to notice.",
    "You have a gift for saying the right thing. Don't lose it.",
  ],
  pragmatic: [
    "Practical as always. You do what needs to be done.",
    "No wasted words, no wasted moves. I respect that.",
    "You're a survivor. That's not an insult — it's the highest compliment here.",
    "The quiet ones last the longest in this world.",
    "You see the board clearly. Most people only see the pieces.",
  ],
  bold: [
    "Direct as always, I see. The samurai are starting to respect that.",
    "Your boldness is going to either save us or get us killed. Probably both.",
    "You speak like someone who's already decided to win.",
    "Thunder tongue! Even the guards straighten up when you talk.",
    "Bold words for a foreigner. But they seem to be working.",
  ],
  hostile: [
    "You're making enemies faster than I can count them...",
    "That sharp tongue of yours is going to cut someone eventually.",
    "Not everyone appreciates honesty delivered like a war hammer.",
    "You know, there IS a middle ground between silence and insult.",
    "The wolves respect you. Everyone else is terrified.",
  ],
  'history-breaking': [
    "The things you say sometimes... it's like you've seen the future.",
    "You shouldn't know these things. But I'm glad you do.",
    "Be careful with that knowledge. It frightens people.",
    "Speaking of things that haven't happened yet... you're playing a dangerous game.",
    "The monks would call you a prophet. The lords would call you a witch. Be careful who hears you.",
  ],
};

// Track hint state
let lastHintCategory = null;
let lastHintRepTotal = 0;
let hintIndex = {}; // per-category index for cycling through hints

/**
 * Check if a Bimbo hint should be shown, and return it if so.
 *
 * @param {Object} reputation - Current reputation tallies
 * @returns {{ category: string, hint: string } | null}
 */
export function checkBimboHint(reputation) {
  if (!reputation) return null;

  // Find dominant category
  let dominant = 'pragmatic';
  let maxVal = 0;
  let totalRep = 0;
  for (const [cat, val] of Object.entries(reputation)) {
    totalRep += val;
    if (val > maxVal) {
      maxVal = val;
      dominant = cat;
    }
  }

  // Trigger conditions:
  // 1. Dominant category shifted from last hint
  // 2. Total reputation increased by >= 2 since last hint
  const categoryShifted = lastHintCategory !== null && dominant !== lastHintCategory;
  const repDelta = totalRep - lastHintRepTotal;
  const shouldHint = categoryShifted || repDelta >= 2;

  if (!shouldHint || maxVal === 0) return null;

  // Get next hint for this category
  const pool = HINT_POOL[dominant] || HINT_POOL.pragmatic;
  const idx = hintIndex[dominant] || 0;
  const hint = pool[idx % pool.length];

  // Update state
  hintIndex[dominant] = (idx + 1) % pool.length;
  lastHintCategory = dominant;
  lastHintRepTotal = totalRep;

  return { category: dominant, hint };
}

/**
 * Reset hint tracking (e.g., on game reset).
 */
export function resetBimboHints() {
  lastHintCategory = null;
  lastHintRepTotal = 0;
  hintIndex = {};
}
