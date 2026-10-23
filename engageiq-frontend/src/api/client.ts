/**
 * EngageIQ API Client
 * Production client connecting directly to the EngageIQ FastAPI PACE backend.
 * Provides end-to-end integration for Organization, Team, Employee, PACE Scores,
 * Human Reviews, CSV Uploads, and Multi-Source Connectors.
 */
import type {
  EmployeeDetail,
  OrgSummary,
  ReviewInput,
  ReviewRecord,
  TeamDetail,
  IntegrationsStatus,
} from './types';

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const USING_SAMPLE_DATA = false;

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    ...init,
  });
  if (!res.ok) {
    let errorDetail = `The server returned an error (${res.status}).`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // fallback to status text
    }
    throw new Error(res.status === 404 ? 'That record was not found.' : errorDetail);
  }
  return (await res.json()) as T;
}

export const api = {
  /** GET /api/organization -> OrgSummary */
  organization: () => http<OrgSummary>('/api/organization'),

  /** GET /api/teams/{teamId} -> TeamDetail */
  team: (teamId: string) => http<TeamDetail>(`/api/teams/${encodeURIComponent(teamId)}`),

  /** GET /api/employees/{employeeId} -> EmployeeDetail */
  employee: (employeeId: string) =>
    http<EmployeeDetail>(`/api/employees/${encodeURIComponent(employeeId)}`),

  /** POST /api/employees/{employeeId}/reviews  body: { outcome, note } -> ReviewRecord */
  submitReview: (input: ReviewInput) =>
    http<ReviewRecord>(
      `/api/employees/${encodeURIComponent(input.employeeId)}/reviews`,
      { method: 'POST', body: JSON.stringify({ outcome: input.outcome, note: input.note }) },
    ),

  /** GET /api/scores -> ScoreRecord[] */
  scores: () => http<any[]>('/api/scores'),

  /** GET /api/integration/status -> IntegrationsStatus */
  integrationsStatus: () => http<IntegrationsStatus>('/api/integration/status'),

  /** POST /api/integration/sync/{connectorId} -> Sync Result */
  syncConnector: (connectorId: string) =>
    http<any>(`/api/integration/sync/${encodeURIComponent(connectorId)}`, { method: 'POST' }),

  /** POST /api/integration/run-aggregation -> Multi-source unified records */
  runAggregation: (daysBack: number = 7) =>
    http<any[]>(`/api/integration/run-aggregation?days_back=${daysBack}`, { method: 'POST' }),

  /** POST /api/integration/webhooks/{source} -> Webhook Receiver */
  sendWebhook: (source: 'slack' | 'github' | 'jira', payload: any) =>
    http<any>(`/api/integration/webhooks/${source}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  /** POST /api/upload -> Upload CSV File */
  uploadCsv: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${BASE}/api/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      let detail = 'Upload failed';
      try {
        const err = await res.json();
        detail = err.detail || detail;
      } catch {}
      throw new Error(detail);
    }
    return await res.json();
  },
};
