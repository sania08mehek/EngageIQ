/**
 * Sample data for building the UI before the backend exists.
 * Everything is generated from a seeded random number generator, so the numbers are the same on every load.
 * Nothing here is imported by the pages directly. They go through client.ts.
 */
import {
  classify,
  clamp01,
  detectPatterns,
  makeWeek,
  mean,
  trendDirection,
  type FeatureReading,
  type WeeklyScore,
} from '../lib/pace';
import { f2 } from '../lib/format';
import type {
  ContributingSignal,
  Employee,
  EmployeeDetail,
  EmployeeRow,
  GroupSummary,
  OrgSummary,
  QueueItem,
  ReviewInput,
  ReviewRecord,
  ReviewStatus,
  RiskAssessment,
  RiskMix,
  RoleId,
  Team,
  TeamDetail,
  TeamRow,
} from './types';

/* ---------- people ---------- */

const TEAMS: Team[] = [
  { id: 'platform', name: 'Platform' },
  { id: 'design', name: 'Product Design' },
  { id: 'sales', name: 'Sales' },
  { id: 'data-ml', name: 'Data and ML' },
];

const ROLE_NAMES: Record<RoleId, string> = {
  engineer: 'Engineer',
  designer: 'Designer',
  salesperson: 'Salesperson',
  manager: 'Manager',
};

type Scenario =
  | 'steadyHigh'
  | 'steadyMid'
  | 'quiet'
  | 'lowSteady'
  | 'collabSlip'
  | 'overload'
  | 'burnout'
  | 'recovering';

interface Spec {
  name: string;
  role: RoleId;
  team: string;
  scenario: Scenario;
}

const SPECS: Spec[] = [
  { name: 'Aarav Nair', role: 'engineer', team: 'platform', scenario: 'steadyHigh' },
  { name: 'Meera Iyer', role: 'engineer', team: 'platform', scenario: 'collabSlip' },
  { name: 'Rohan Das', role: 'engineer', team: 'platform', scenario: 'overload' },
  { name: 'Kavya Menon', role: 'manager', team: 'platform', scenario: 'steadyMid' },

  { name: 'Ananya Rao', role: 'designer', team: 'design', scenario: 'steadyHigh' },
  { name: 'Ishaan Bose', role: 'designer', team: 'design', scenario: 'quiet' },
  { name: 'Zoya Khan', role: 'designer', team: 'design', scenario: 'recovering' },
  { name: 'Neel Kapoor', role: 'manager', team: 'design', scenario: 'steadyHigh' },

  { name: 'Farhan Ali', role: 'salesperson', team: 'sales', scenario: 'burnout' },
  { name: 'Tara Joshi', role: 'salesperson', team: 'sales', scenario: 'steadyMid' },
  { name: 'Vikram Shah', role: 'salesperson', team: 'sales', scenario: 'steadyHigh' },
  { name: 'Sana Pillai', role: 'manager', team: 'sales', scenario: 'steadyMid' },

  { name: 'Arjun Reddy', role: 'engineer', team: 'data-ml', scenario: 'steadyHigh' },
  { name: 'Divya Krishnan', role: 'engineer', team: 'data-ml', scenario: 'quiet' },
  { name: 'Kabir Sheikh', role: 'engineer', team: 'data-ml', scenario: 'lowSteady' },
  { name: 'Leela George', role: 'manager', team: 'data-ml', scenario: 'steadyHigh' },
];

/* ---------- weeks and scenarios ---------- */

const WEEK_COUNT = 12;
/** Monday of the latest complete week */
const LAST_WEEK = Date.UTC(2026, 8, 14);
const WEEKS: string[] = Array.from({ length: WEEK_COUNT }, (_, i) => {
  const d = new Date(LAST_WEEK - (WEEK_COUNT - 1 - i) * 7 * 86400000);
  return d.toISOString().slice(0, 10);
});

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const ramp = (i: number, from: number, to: number) => clamp01((i - from) / (to - from));

type Noise = (amplitude: number) => number;
type Curve = (i: number, n: Noise) => { ehs: number; opi: number };

const CURVES: Record<Scenario, Curve> = {
  steadyHigh: (_i, n) => ({ ehs: 0.78 + n(0.03), opi: 0.83 + n(0.03) }),
  steadyMid: (_i, n) => ({ ehs: 0.68 + n(0.02), opi: 0.76 + n(0.02) }),
  // slow to reply, few meetings, excellent delivery
  quiet: (_i, n) => ({ ehs: 0.45 + n(0.02), opi: 0.9 + n(0.015) }),
  lowSteady: (_i, n) => ({ ehs: 0.55 + n(0.015), opi: 0.62 + n(0.015) }),
  // the pattern from the architecture doc: collaboration falls while output stays flat
  collabSlip: (i, n) => ({ ehs: lerp(0.78, 0.5, ramp(i, 7, 11)) + n(0.01), opi: 0.8 + n(0.01) }),
  overload: (i, n) => ({
    ehs: lerp(0.74, 0.44, ramp(i, 5, 11)) + n(0.01),
    opi: lerp(0.8, 0.58, ramp(i, 5, 11)) + n(0.01),
  }),
  burnout: (i, n) => ({
    ehs: lerp(0.72, 0.3, ramp(i, 4, 11)) + n(0.01),
    opi: lerp(0.78, 0.4, ramp(i, 4, 11)) + n(0.01),
  }),
  recovering: (i, n) => ({
    ehs: lerp(0.48, 0.72, ramp(i, 3, 11)) + n(0.01),
    opi: lerp(0.66, 0.8, ramp(i, 3, 11)) + n(0.01),
  }),
};

function seeded(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const hash = (s: string) => [...s].reduce((h, c) => (Math.imul(h, 31) + c.charCodeAt(0)) >>> 0, 7);
const slug = (name: string) => name.toLowerCase().replace(/[^a-z]+/g, '-');

/* ---------- role-aware features ---------- */

interface MetaDef {
  key: string;
  label: string;
  unit: string;
  dir: FeatureReading['dir'];
  decimals: number;
}
interface OutputDef extends MetaDef {
  base: number;
  cap?: number;
}

const SIGNAL_META: MetaDef[] = [
  { key: 'meetingHours', label: 'Meeting load', unit: 'hrs/week', dir: 'lower', decimals: 1 },
  { key: 'focusGapDays', label: 'Focus-time gap', unit: 'days/week', dir: 'lower', decimals: 1 },
  { key: 'responseHours', label: 'Response latency', unit: 'hrs', dir: 'lower', decimals: 1 },
  { key: 'afterHoursPct', label: 'After-hours activity', unit: '% of work', dir: 'lower', decimals: 1 },
];

const EFFORT: OutputDef = { key: 'effort', label: 'Self-reported effort', unit: 'of 5', dir: 'neutral', decimals: 1, base: 3.6, cap: 5 };

const ROLE_OUTPUTS: Record<RoleId, OutputDef[]> = {
  engineer: [
    { key: 'taskCompletion', label: 'Task completion', unit: '%', dir: 'higher', decimals: 0, base: 88, cap: 100 },
    { key: 'deadlinePct', label: 'Deadline adherence', unit: '%', dir: 'higher', decimals: 0, base: 90, cap: 100 },
    { key: 'commits', label: 'Commits', unit: '/week', dir: 'higher', decimals: 0, base: 34 },
    { key: 'prs', label: 'Pull requests', unit: '/week', dir: 'higher', decimals: 1, base: 6 },
    { key: 'rework', label: 'Rework', unit: '% reopened', dir: 'lower', decimals: 1, base: 9 },
    EFFORT,
  ],
  designer: [
    { key: 'deliverables', label: 'Deliverables shipped', unit: '/week', dir: 'higher', decimals: 1, base: 5 },
    { key: 'deadlinePct', label: 'Deadline adherence', unit: '%', dir: 'higher', decimals: 0, base: 88, cap: 100 },
    { key: 'revisions', label: 'Revision rounds', unit: 'per deliverable', dir: 'lower', decimals: 1, base: 1.8 },
    EFFORT,
  ],
  salesperson: [
    { key: 'target', label: 'Target completion', unit: '%', dir: 'higher', decimals: 0, base: 92, cap: 120 },
    { key: 'crm', label: 'CRM updates', unit: '/week', dir: 'higher', decimals: 0, base: 42 },
    { key: 'followups', label: 'Follow-ups on time', unit: '%', dir: 'higher', decimals: 0, base: 86, cap: 100 },
    EFFORT,
  ],
  manager: [
    { key: 'teamDelivery', label: 'Team delivery', unit: '% of goals', dir: 'higher', decimals: 0, base: 87, cap: 100 },
    { key: 'planning', label: 'Planning on time', unit: '%', dir: 'higher', decimals: 0, base: 91, cap: 100 },
    { key: 'blockers', label: 'Blockers cleared', unit: '/week', dir: 'higher', decimals: 1, base: 9 },
    EFFORT,
  ],
};

function signalValues(ehs: number): Record<string, number> {
  const d = 0.75 - ehs;
  return {
    meetingHours: Math.max(3, 12 * (1 + d * 1.6)),
    focusGapDays: Math.max(0, 1 + d * 6),
    responseHours: Math.max(0.5, 3 * (1 + d * 2.2)),
    afterHoursPct: Math.max(1, 8 * (1 + d * 3.5)),
  };
}

function outputValue(def: OutputDef, opi: number): number {
  let v: number;
  if (def.dir === 'lower') v = def.base * Math.max(0.6, 1 + (0.82 - opi) * 3);
  else if (def.dir === 'neutral') v = def.base * (1 + (0.82 - opi) * 0.5);
  else v = def.base * Math.min(1.25, Math.max(0.4, opi / 0.82));
  return def.cap ? Math.min(def.cap, v) : v;
}

/* ---------- build each person ---------- */

interface Base {
  employee: Employee;
  history: WeeklyScore[];
  features: FeatureReading[];
  risk: RiskAssessment;
  flagged: boolean;
  baselinePace: number;
}

function buildFeatures(role: RoleId, history: WeeklyScore[]): FeatureReading[] {
  const split = history.length - 4;
  const summarize = (values: number[]) => ({
    baseline: mean(values.slice(0, split)),
    value: mean(values.slice(split)),
  });

  const out: FeatureReading[] = [];
  for (const meta of SIGNAL_META) {
    const s = summarize(history.map((w) => signalValues(w.ehs)[meta.key]));
    out.push({ ...meta, layer: 'signal', ...s });
  }
  for (const def of ROLE_OUTPUTS[role]) {
    const s = summarize(history.map((w) => outputValue(def, w.opi)));
    const { base: _base, cap: _cap, ...meta } = def;
    out.push({ ...meta, layer: 'output', ...s });
  }
  return out;
}

function contributing(features: FeatureReading[]): ContributingSignal[] {
  return features
    .filter((f) => f.dir !== 'neutral' && f.baseline)
    .map((f) => ({ f, rel: (f.value - f.baseline) / f.baseline }))
    .filter(({ f, rel }) => (f.dir === 'higher' ? rel < -0.05 : rel > 0.08))
    .sort((a, b) => Math.abs(b.rel) - Math.abs(a.rel))
    .slice(0, 4)
    .map(({ f, rel }) => ({
      key: f.key,
      label: f.label,
      layer: f.layer,
      text: `${f.value.toFixed(f.decimals)} ${f.unit} now, usually ${f.baseline.toFixed(f.decimals)} (${rel > 0 ? '+' : '\u2212'}${Math.abs(Math.round(rel * 100))}%)`,
    }));
}

function assess(history: WeeklyScore[], features: FeatureReading[]): RiskAssessment {
  const latest = history[history.length - 1];
  const category = classify(latest.pace);
  const patterns = detectPatterns(history);
  let summary: string;
  if (patterns.length) summary = patterns[0].detail;
  else if (category === 'at-risk') summary = `PACE is ${f2(latest.pace)}, below the 0.40 line. A supportive check-in is a good next step.`;
  else if (category === 'moderate') summary = 'PACE is in the moderate range and holding steady. Worth keeping an eye on.';
  else summary = 'Work patterns and delivery are steady. Nothing to act on.';

  return {
    category,
    riskScore: Math.round((1 - latest.pace) * 100) / 100,
    trend: trendDirection(history),
    patterns,
    contributing: contributing(features),
    evidenceWeeks: history.length,
    summary,
  };
}

function build(spec: Spec): Base {
  const id = slug(spec.name);
  const rand = seeded(hash(id));
  const noise: Noise = (a) => (rand() * 2 - 1) * a;
  const history = WEEKS.map((week, i) => {
    const { ehs, opi } = CURVES[spec.scenario](i, noise);
    return makeWeek(week, clamp01(ehs), clamp01(opi));
  });
  const team = TEAMS.find((t) => t.id === spec.team) as Team;
  const features = buildFeatures(spec.role, history);
  const risk = assess(history, features);
  return {
    employee: { id, name: spec.name, roleId: spec.role, roleName: ROLE_NAMES[spec.role], teamId: team.id, teamName: team.name },
    history,
    features,
    risk,
    flagged: risk.patterns.length > 0 || risk.category === 'at-risk',
    baselinePace: mean(history.slice(0, -4).map((w) => w.pace)),
  };
}

const BASES: Base[] = SPECS.map(build);

/* ---------- human reviews (kept in the browser while the backend does not exist) ---------- */

const STORAGE_KEY = 'engageiq.sample.reviews';
const SEED_REVIEWS: ReviewRecord[] = [
  {
    id: 'seed-1',
    employeeId: 'kabir-sheikh',
    outcome: 'check-blockers',
    note: 'Waiting on data access from the platform team. Followed up with them.',
    reviewer: 'Manager',
    at: '2026-08-31T10:00:00.000Z',
    flagWeek: '2026-08-24',
  },
];

function loadReviews(): ReviewRecord[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as ReviewRecord[];
  } catch {
    /* storage unavailable, use the seed */
  }
  return SEED_REVIEWS.slice();
}

let reviews: ReviewRecord[] = loadReviews();

function persistReviews() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(reviews));
  } catch {
    /* ignore */
  }
}

function reviewsFor(id: string): ReviewRecord[] {
  return reviews.filter((r) => r.employeeId === id).sort((a, b) => b.at.localeCompare(a.at));
}

function statusOf(b: Base): ReviewStatus {
  if (!b.flagged) return 'not-flagged';
  const week = b.history[b.history.length - 1].week;
  return reviews.some((r) => r.employeeId === b.employee.id && r.flagWeek === week) ? 'reviewed' : 'needs-review';
}

/* ---------- views ---------- */

const last = <T,>(xs: T[]) => xs[xs.length - 1];
const deltaOf = (history: WeeklyScore[]) => last(history).pace - history[history.length - 5].pace;

function rowOf(b: Base): EmployeeRow {
  return {
    employee: b.employee,
    latest: last(b.history),
    delta: deltaOf(b.history),
    category: b.risk.category,
    trend: b.risk.trend,
    sparkline: b.history.slice(-8).map((w) => w.pace),
    flagged: b.flagged,
    reviewStatus: statusOf(b),
  };
}

function summarize(members: Base[]): GroupSummary {
  const history = WEEKS.map((week, i) =>
    makeWeek(week, mean(members.map((m) => m.history[i].ehs)), mean(members.map((m) => m.history[i].opi))),
  );
  const mix: RiskMix = { healthy: 0, moderate: 0, 'at-risk': 0 };
  members.forEach((m) => (mix[m.risk.category] += 1));
  return { headcount: members.length, history, latest: last(history), delta: deltaOf(history), mix };
}

function queueOf(members: Base[]): QueueItem[] {
  return members
    .filter((b) => b.flagged)
    .map((b): QueueItem => {
      const status = statusOf(b) === 'reviewed' ? 'reviewed' : 'needs-review';
      const latestReview = reviewsFor(b.employee.id)[0];
      return {
        employee: b.employee,
        category: b.risk.category,
        pace: last(b.history).pace,
        headline: b.risk.patterns[0]?.title ?? 'PACE is in the at-risk range',
        status,
        lastOutcome: status === 'reviewed' ? latestReview?.outcome : undefined,
      };
    })
    .sort((a, b) => (a.status === b.status ? a.pace - b.pace : a.status === 'needs-review' ? -1 : 1));
}

export function organization(): OrgSummary {
  const teams: TeamRow[] = TEAMS.map((team) => {
    const members = BASES.filter((b) => b.employee.teamId === team.id);
    return { team, ...summarize(members), sparkline: summarize(members).history.slice(-8).map((w) => w.pace) };
  });
  return { ...summarize(BASES), teams, queue: queueOf(BASES) };
}

export function team(teamId: string): TeamDetail {
  const t = TEAMS.find((x) => x.id === teamId);
  if (!t) throw new Error('Team not found');
  const members = BASES.filter((b) => b.employee.teamId === teamId);
  return { team: t, ...summarize(members), members: members.map(rowOf), queue: queueOf(members) };
}

export function employee(id: string): EmployeeDetail {
  const b = BASES.find((x) => x.employee.id === id);
  if (!b) throw new Error('Person not found');
  return {
    employee: b.employee,
    history: b.history,
    latest: last(b.history),
    delta: deltaOf(b.history),
    baselinePace: b.baselinePace,
    features: b.features,
    risk: b.risk,
    reviews: reviewsFor(id),
    reviewStatus: statusOf(b),
  };
}

export function addReview(input: ReviewInput): ReviewRecord {
  const b = BASES.find((x) => x.employee.id === input.employeeId);
  if (!b) throw new Error('Person not found');
  const record: ReviewRecord = {
    id: `r-${Date.now()}`,
    employeeId: input.employeeId,
    outcome: input.outcome,
    note: input.note.trim(),
    reviewer: 'Manager',
    at: new Date().toISOString(),
    flagWeek: last(b.history).week,
  };
  reviews = [record, ...reviews];
  persistReviews();
  return record;
}

