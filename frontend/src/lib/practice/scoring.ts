export type Band = 'green' | 'yellow' | 'red';

export type Scores = {
  grammatical: number;
  natural: number;
  register: number;
  meaning: number;
};

function clamp01(s: number): number {
  return Math.min(1, Math.max(0, s));
}

export function scoreToBand(s: number): Band {
  const c = clamp01(s);
  if (c >= 0.7) return 'green';
  if (c >= 0.4) return 'yellow';
  return 'red';
}

export function scoreToPercent(s: number): number {
  return Math.round(clamp01(s) * 100);
}

export function bandColorHex(b: Band): string {
  switch (b) {
    case 'green':
      return '#22c55e';
    case 'yellow':
      return '#eab308';
    case 'red':
      return '#ef4444';
  }
}

export function worstDimension(s: Scores): keyof Scores | null {
  const entries = Object.entries(s) as [keyof Scores, number][];
  let worstKey: keyof Scores | null = null;
  let worstValue = Infinity;
  for (const [key, value] of entries) {
    if (value < worstValue) {
      worstValue = value;
      worstKey = key;
    }
  }
  if (worstKey === null || worstValue >= 0.7) return null;
  return worstKey;
}
