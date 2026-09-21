import { describe, it, expect } from 'vitest';

// Contract for UI helpers in $lib/practice/scoring.ts. Pure functions
// mapping calibrated Jev scores (0..1) onto display primitives.
//
// Bands (see WIP):
//   score >= 0.7 → 'green'   (native-adjacent)
//   score >= 0.4 → 'yellow'  (understandable, needs polish)
//   score <  0.4 → 'red'     (learner should try again)

import {
  scoreToBand,
  scoreToPercent,
  bandColorHex,
  type Band,
  type Scores,
  worstDimension,
} from '$lib/practice/scoring';

describe('scoreToBand', () => {
  it('green >= 0.7', () => {
    expect(scoreToBand(0.7)).toBe('green');
    expect(scoreToBand(0.95)).toBe('green');
  });
  it('yellow in [0.4, 0.7)', () => {
    expect(scoreToBand(0.4)).toBe('yellow');
    expect(scoreToBand(0.69)).toBe('yellow');
  });
  it('red < 0.4', () => {
    expect(scoreToBand(0)).toBe('red');
    expect(scoreToBand(0.39)).toBe('red');
  });
  it('clamps out-of-range gracefully', () => {
    expect(scoreToBand(-0.1)).toBe('red');
    expect(scoreToBand(1.5)).toBe('green');
  });
});

describe('scoreToPercent', () => {
  it('0..1 → 0..100 integer', () => {
    expect(scoreToPercent(0)).toBe(0);
    expect(scoreToPercent(0.5)).toBe(50);
    expect(scoreToPercent(0.756)).toBe(76);
    expect(scoreToPercent(1)).toBe(100);
  });
});

describe('bandColorHex', () => {
  it('returns three distinct hex strings', () => {
    const g = bandColorHex('green' as Band);
    const y = bandColorHex('yellow' as Band);
    const r = bandColorHex('red' as Band);
    expect(g).toMatch(/^#[0-9a-f]{6}$/i);
    expect(y).toMatch(/^#[0-9a-f]{6}$/i);
    expect(r).toMatch(/^#[0-9a-f]{6}$/i);
    expect(new Set([g, y, r]).size).toBe(3);
  });
});

describe('worstDimension', () => {
  it('returns the dim with the lowest score', () => {
    const s: Scores = { grammatical: 0.9, natural: 0.5, register: 0.85, meaning: 0.8 };
    expect(worstDimension(s)).toBe('natural');
  });
  it('all green → returns null (nothing to fix)', () => {
    const s: Scores = { grammatical: 0.9, natural: 0.85, register: 0.8, meaning: 0.95 };
    expect(worstDimension(s)).toBeNull();
  });
});
