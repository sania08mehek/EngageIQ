import { clamp01, mean, WEIGHTS, type Layer } from './pace';

/**
 * Feature definitions used by the PACE calculator.
 * The architecture doc names the measures but not how each one becomes a 0 to 1 "health" value,
 * so the ranges below are placeholders. Replace them with the backend's role-aware configuration.
 * Inside each layer every feature currently counts equally.
 */
export type FeatureKey =
  | 'meetingHours'
  | 'focusGapDays'
  | 'responseHours'
  | 'afterHoursPct'
  | 'taskCompletion'
  | 'velocityPct'
  | 'deadlinePct'
  | 'activityPct'
  | 'effort'
  | 'reworkPct';

export type Inputs = Record<FeatureKey, number>;

export interface FeatureDef {
  key: FeatureKey;
  layer: Layer;
  label: string;
  hint: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  toHealth: (v: number) => number;
}

export const FEATURES: FeatureDef[] = [
  {
    key: 'meetingHours', layer: 'signal', label: 'Meeting load', unit: 'hours a week',
    hint: 'Full marks up to 8 hours, zero at 25 or more.',
    min: 0, max: 35, step: 1, toHealth: (v) => clamp01((25 - v) / 17),
  },
  {
    key: 'focusGapDays', layer: 'signal', label: 'Focus-time gap', unit: 'days without a 2-hour block',
    hint: 'Days in the week with no uninterrupted 2-hour stretch.',
    min: 0, max: 5, step: 1, toHealth: (v) => clamp01(1 - v / 5),
  },
  {
    key: 'responseHours', layer: 'signal', label: 'Response latency', unit: 'hours to reply',
    hint: 'Median reply time. Full marks at 1 hour, zero at 12 or more.',
    min: 0, max: 24, step: 0.5, toHealth: (v) => clamp01((12 - v) / 11),
  },
  {
    key: 'afterHoursPct', layer: 'signal', label: 'After-hours activity', unit: '% of work',
    hint: 'Share of work outside expected hours. Full marks up to 5%, zero at 30%.',
    min: 0, max: 50, step: 1, toHealth: (v) => clamp01((30 - v) / 25),
  },
  {
    key: 'taskCompletion', layer: 'output', label: 'Task completion', unit: '% of planned tasks',
    hint: 'Completed work items against plan.',
    min: 0, max: 100, step: 1, toHealth: (v) => clamp01(v / 100),
  },
  {
    key: 'velocityPct', layer: 'output', label: 'Sprint velocity', unit: '% of own usual',
    hint: 'Delivery across the sprint, against their own baseline.',
    min: 0, max: 150, step: 1, toHealth: (v) => clamp01(v / 100),
  },
  {
    key: 'deadlinePct', layer: 'output', label: 'Deadline adherence', unit: '% on time',
    hint: 'Work delivered by the expected date.',
    min: 0, max: 100, step: 1, toHealth: (v) => clamp01(v / 100),
  },
  {
    key: 'activityPct', layer: 'output', label: 'Commits and pull requests', unit: '% of own usual',
    hint: 'Engineer measure. Other roles use their own delivery measures.',
    min: 0, max: 150, step: 1, toHealth: (v) => clamp01(v / 100),
  },
  {
    key: 'effort', layer: 'output', label: 'Self-reported effort', unit: 'out of 5',
    hint: 'What the person says they put in. 1 is low, 5 is high.',
    min: 1, max: 5, step: 0.5, toHealth: (v) => clamp01((v - 1) / 4),
  },
  {
    key: 'reworkPct', layer: 'output', label: 'Rework', unit: '% reopened',
    hint: 'Work that had to be redone. Full marks up to 5%, zero at 35%.',
    min: 0, max: 50, step: 1, toHealth: (v) => clamp01((35 - v) / 30),
  },
];

export const SIGNAL_FEATURES = FEATURES.filter((f) => f.layer === 'signal');
export const OUTPUT_FEATURES = FEATURES.filter((f) => f.layer === 'output');

export function computeIndices(inputs: Inputs): { ehs: number; opi: number; pace: number } {
  const ehs = mean(SIGNAL_FEATURES.map((f) => f.toHealth(inputs[f.key])));
  const opi = mean(OUTPUT_FEATURES.map((f) => f.toHealth(inputs[f.key])));
  return { ehs, opi, pace: WEIGHTS.ehs * ehs + WEIGHTS.opi * opi };
}

/* ---------- Presets: four-week stories that show what the trend engine looks for ---------- */

export type PresetId = 'steady' | 'quiet' | 'slipping' | 'overloaded';

export interface Preset {
  id: PresetId;
  name: string;
  blurb: string;
  weeks: Inputs[];
}

const patch = (base: Inputs, p: Partial<Inputs>): Inputs => ({ ...base, ...p });

const steady: Inputs = {
  meetingHours: 12, focusGapDays: 1, responseHours: 3, afterHoursPct: 8,
  taskCompletion: 88, velocityPct: 100, deadlinePct: 90, activityPct: 100, effort: 3.5, reworkPct: 8,
};

const steadyOutput: Partial<Inputs> = {
  taskCompletion: 84, velocityPct: 92, deadlinePct: 86, activityPct: 95, effort: 3.5, reworkPct: 10,
};
const slipBase = patch(steady, steadyOutput);

const quiet: Inputs = {
  meetingHours: 10, focusGapDays: 3, responseHours: 14, afterHoursPct: 15,
  taskCompletion: 96, velocityPct: 110, deadlinePct: 97, activityPct: 110, effort: 3.5, reworkPct: 4,
};

export const PRESETS: Preset[] = [
  {
    id: 'steady',
    name: 'Steady delivery',
    blurb: 'Healthy patterns and solid output. Nothing should be flagged.',
    weeks: [
      steady,
      patch(steady, { meetingHours: 13, responseHours: 3.5 }),
      patch(steady, { meetingHours: 11, taskCompletion: 90 }),
      patch(steady, { afterHoursPct: 9 }),
    ],
  },
  {
    id: 'quiet',
    name: 'Quiet collaborator',
    blurb: 'Slow replies and scattered focus, but excellent delivery. The 60/40 weighting keeps this person Healthy.',
    weeks: [
      quiet,
      patch(quiet, { responseHours: 13, taskCompletion: 95 }),
      patch(quiet, { responseHours: 15, deadlinePct: 96 }),
      patch(quiet, { meetingHours: 9, afterHoursPct: 14 }),
    ],
  },
  {
    id: 'slipping',
    name: 'Collaboration slipping',
    blurb: 'Work patterns decline week by week while delivery holds. Only a trend view catches this.',
    weeks: [
      slipBase,
      patch(slipBase, { meetingHours: 14, focusGapDays: 1, responseHours: 4, afterHoursPct: 10 }),
      patch(slipBase, { meetingHours: 16, focusGapDays: 2, responseHours: 5.5, afterHoursPct: 13 }),
      patch(slipBase, { meetingHours: 18, focusGapDays: 2, responseHours: 7, afterHoursPct: 16 }),
    ],
  },
  {
    id: 'overloaded',
    name: 'Overloaded',
    blurb: 'More meetings and late work, with delivery and quality dropping alongside.',
    weeks: [
      steady,
      patch(steady, {
        meetingHours: 16, focusGapDays: 2, responseHours: 5, afterHoursPct: 14,
        taskCompletion: 82, velocityPct: 90, deadlinePct: 84, activityPct: 90, effort: 4, reworkPct: 10,
      }),
      patch(steady, {
        meetingHours: 20, focusGapDays: 3, responseHours: 7, afterHoursPct: 20,
        taskCompletion: 74, velocityPct: 80, deadlinePct: 74, activityPct: 80, effort: 4.5, reworkPct: 16,
      }),
      patch(steady, {
        meetingHours: 23, focusGapDays: 4, responseHours: 9, afterHoursPct: 26,
        taskCompletion: 66, velocityPct: 70, deadlinePct: 64, activityPct: 70, effort: 4.5, reworkPct: 22,
      }),
    ],
  },
];

export function clonePreset(id: PresetId): Inputs[] {
  const preset = PRESETS.find((p) => p.id === id) ?? PRESETS[0];
  return preset.weeks.map((w) => ({ ...w }));
}
