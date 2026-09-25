import type {
  FeatureReading,
  Pattern,
  RiskCategory,
  TrendDirection,
  WeeklyScore,
} from '../lib/pace';

/**
 * Response shapes the UI expects. When you build the FastAPI backend, return these
 * (field names map to the tables in the architecture doc: employees, pace_scores,
 * signal_metrics, output_metrics, risk_events).
 */

export type RoleId = 'engineer' | 'designer' | 'salesperson' | 'manager';

export interface Team {
  id: string;
  name: string;
}

export interface Employee {
  id: string;
  name: string;
  roleId: RoleId;
  roleName: string;
  teamId: string;
  teamName: string;
}

export type ReviewOutcome =
  | 'no-concern'
  | 'monitor-trend'
  | 'discuss-workload'
  | 'check-blockers'
  | 'offer-support'
  | 'correct-data'
  | 'override-signal';

export const REVIEW_OUTCOMES: { id: ReviewOutcome; label: string; hint: string }[] = [
  { id: 'no-concern', label: 'No concern', hint: 'The pattern has a clear, harmless explanation.' },
  { id: 'monitor-trend', label: 'Monitor trend', hint: 'Keep watching for a few more weeks.' },
  { id: 'discuss-workload', label: 'Discuss workload', hint: 'Talk about load, priorities or deadlines.' },
  { id: 'check-blockers', label: 'Check project blockers', hint: 'Look for blocked work or missing access.' },
  { id: 'offer-support', label: 'Offer support', hint: 'Reach out with help or time off.' },
  { id: 'correct-data', label: 'Correct a data issue', hint: 'A connector or record looks wrong.' },
  { id: 'override-signal', label: 'Override the risk signal', hint: 'Dismiss this signal and record why.' },
];

export const outcomeLabel = (id: ReviewOutcome) => REVIEW_OUTCOMES.find((o) => o.id === id)?.label ?? id;

export interface ReviewRecord {
  id: string;
  employeeId: string;
  outcome: ReviewOutcome;
  note: string;
  reviewer: string;
  /** ISO timestamp */
  at: string;
  /** The week of the score that was reviewed. A review counts for the flag raised in that week. */
  flagWeek: string;
}

export interface ReviewInput {
  employeeId: string;
  outcome: ReviewOutcome;
  note: string;
}

export type ReviewStatus = 'not-flagged' | 'needs-review' | 'reviewed';
export type RiskMix = Record<RiskCategory, number>;

export interface ContributingSignal {
  key: string;
  label: string;
  layer: 'signal' | 'output';
  text: string;
}

export interface RiskAssessment {
  category: RiskCategory;
  /** 1 minus PACE, so higher means more concern */
  riskScore: number;
  trend: TrendDirection;
  patterns: Pattern[];
  contributing: ContributingSignal[];
  /** number of weekly scores the assessment is based on */
  evidenceWeeks: number;
  summary: string;
}

export interface EmployeeRow {
  employee: Employee;
  latest: WeeklyScore;
  /** PACE now minus PACE 4 weeks ago */
  delta: number;
  category: RiskCategory;
  trend: TrendDirection;
  sparkline: number[];
  flagged: boolean;
  reviewStatus: ReviewStatus;
}

export interface EmployeeDetail {
  employee: Employee;
  history: WeeklyScore[];
  latest: WeeklyScore;
  delta: number;
  /** the person's average PACE before the latest 4 weeks */
  baselinePace: number;
  features: FeatureReading[];
  risk: RiskAssessment;
  reviews: ReviewRecord[];
  reviewStatus: ReviewStatus;
}

export interface GroupSummary {
  headcount: number;
  history: WeeklyScore[];
  latest: WeeklyScore;
  delta: number;
  mix: RiskMix;
}

export interface TeamRow extends GroupSummary {
  team: Team;
  sparkline: number[];
}

export interface QueueItem {
  employee: Employee;
  category: RiskCategory;
  pace: number;
  headline: string;
  status: 'needs-review' | 'reviewed';
  lastOutcome?: ReviewOutcome;
}

export interface OrgSummary extends GroupSummary {
  teams: TeamRow[];
  queue: QueueItem[];
}

export interface TeamDetail extends GroupSummary {
  team: Team;
  members: EmployeeRow[];
  queue: QueueItem[];
}
