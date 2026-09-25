import { f2, signed } from './format';

export type RiskCategory = 'healthy' | 'moderate' | 'at-risk';
export type Layer = 'signal' | 'output';
export type TrendDirection = 'up' | 'flat' | 'down';

/** PACE = 0.4 x EHS + 0.6 x OPI  (architecture doc, section 4) */
export const WEIGHTS = { ehs: 0.4, opi: 0.6 } as const;

/** Presentation-level risk bands (architecture doc, section 15). Validate on real data before using operationally. */
export const BANDS: { id: RiskCategory; label: string; min: number; max: number }[] = [
  { id: 'healthy', label: 'Healthy', min: 0.7, max: 1 },
  { id: 'moderate', label: 'Moderate', min: 0.4, max: 0.7 },
  { id: 'at-risk', label: 'At-risk', min: 0, max: 0.4 },
];

export const CATEGORY_LABEL: Record<RiskCategory, string> = {
  healthy: 'Healthy',
  moderate: 'Moderate',
  'at-risk': 'At-risk',
};

export interface WeeklyScore {
  /** ISO date of the Monday that starts the week */
  week: string;
  ehs: number;
  opi: number;
  pace: number;
}

export interface Pattern {
  id: 'collab-down-output-flat' | 'both-layers-down' | 'persistent-decline' | 'sudden-change';
  title: string;
  detail: string;
}

export interface FeatureReading {
  key: string;
  label: string;
  layer: Layer;
  unit: string;
  /** average over the last 4 weeks */
  value: number;
  /** the person's own usual level (earlier weeks) */
  baseline: number;
  /** which direction is healthier. Neutral measures are shown but never flagged. */
  dir: 'higher' | 'lower' | 'neutral';
  decimals: number;
}

export const clamp01 = (n: number) => Math.min(1, Math.max(0, n));
export const mean = (xs: number[]) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0);

export function paceScore(ehs: number, opi: number): number {
  return WEIGHTS.ehs * ehs + WEIGHTS.opi * opi;
}

export function classify(pace: number): RiskCategory {
  const p = Math.round(pace * 1000) / 1000; // avoid 0.6999999 landing in the wrong band
  if (p >= 0.7) return 'healthy';
  if (p >= 0.4) return 'moderate';
  return 'at-risk';
}

export function makeWeek(week: string, ehs: number, opi: number): WeeklyScore {
  return { week, ehs, opi, pace: paceScore(ehs, opi) };
}

export function trendDirection(history: WeeklyScore[]): TrendDirection {
  if (history.length < 4) return 'flat';
  const recent = mean(history.slice(-2).map((w) => w.pace));
  const before = mean(history.slice(-4, -2).map((w) => w.pace));
  const d = recent - before;
  return d > 0.02 ? 'up' : d < -0.02 ? 'down' : 'flat';
}

/**
 * Simple statistical trend engine for the MVP (architecture doc, section 14).
 * It compares the latest 4 weeks with the person's own history.
 * Swap this for the backend's anomaly detection when it exists; the UI only needs Pattern[].
 */
export function detectPatterns(history: WeeklyScore[]): Pattern[] {
  const out: Pattern[] = [];
  if (history.length < 4) return out;

  const recent = history.slice(-4);
  const earlier = history.slice(0, -4);
  const first = recent[0];
  const last = recent[recent.length - 1];

  const ehsDrop = first.ehs - last.ehs;
  const opiDrop = first.opi - last.opi;
  const ehsSteadyDecline = recent.every((w, i) => i === 0 || w.ehs <= recent[i - 1].ehs + 0.02);

  if (ehsDrop >= 0.1 && ehsSteadyDecline && Math.abs(opiDrop) <= 0.05) {
    const opiMove = Math.abs(opiDrop) < 0.005 ? 'stayed level' : `moved only ${f2(Math.abs(opiDrop))}`;
    out.push({
      id: 'collab-down-output-flat',
      title: 'Collaboration health falling, delivery steady',
      detail: `Work-pattern health (EHS) fell ${f2(ehsDrop)} over 4 weeks while output (OPI) ${opiMove}. This can be an early sign of strain that delivery numbers do not show yet.`,
    });
  }

  if (ehsDrop >= 0.08 && opiDrop >= 0.08) {
    out.push({
      id: 'both-layers-down',
      title: 'Work patterns and delivery both falling',
      detail: `EHS fell ${f2(ehsDrop)} and OPI fell ${f2(opiDrop)} over 4 weeks. Heavier load and slipping delivery often show up together.`,
    });
  }

  const lastThree = recent.slice(-3);
  const paceDrop = first.pace - last.pace;
  if (lastThree.every((w) => w.pace < 0.7) && paceDrop >= 0.04) {
    out.push({
      id: 'persistent-decline',
      title: 'Below the healthy range and still dropping',
      detail: `PACE has stayed under 0.70 for 3 weeks and is ${f2(paceDrop)} lower than 4 weeks ago.`,
    });
  }

  const baseline = earlier.length >= 3 ? mean(earlier.map((w) => w.pace)) : history[0].pace;
  if (baseline - last.pace >= 0.12) {
    out.push({
      id: 'sudden-change',
      title: 'Sharp move away from their usual level',
      detail: `Latest PACE (${f2(last.pace)}) is ${f2(baseline - last.pace)} below this person's own earlier average (${f2(baseline)}).`,
    });
  }

  return out;
}

/** How a measure moved against the person's own baseline. */
export function featureChange(f: FeatureReading): { pct: number; label: string; tone: 'better' | 'worse' | 'neutral' } {
  const rel = f.baseline ? (f.value - f.baseline) / f.baseline : 0;
  let tone: 'better' | 'worse' | 'neutral' = 'neutral';
  if (f.dir === 'higher') tone = rel > 0.05 ? 'better' : rel < -0.05 ? 'worse' : 'neutral';
  if (f.dir === 'lower') tone = rel < -0.05 ? 'better' : rel > 0.08 ? 'worse' : 'neutral';
  const pct = Math.round(rel * 100);
  return { pct, label: `${signed(pct, 0)}%`, tone };
}
