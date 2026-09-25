/**
 * The only file the pages use to get data.
 *
 * Right now every call returns sample data from mock.ts.
 * When your FastAPI backend is ready, set VITE_API_URL (see .env.example) and the same calls
 * go over HTTP instead. Each function lists the endpoint it expects and the type it should return.
 */
import * as mock from './mock';
import type { EmployeeDetail, OrgSummary, ReviewInput, ReviewRecord, TeamDetail } from './types';

const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || '';

export const USING_SAMPLE_DATA = !BASE;

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    ...init,
  });
  if (!res.ok) {
    throw new Error(res.status === 404 ? 'That record was not found.' : `The server returned an error (${res.status}).`);
  }
  return (await res.json()) as T;
}

const pause = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function call<T>(path: string, sample: () => T, init?: RequestInit): Promise<T> {
  if (BASE) return http<T>(path, init);
  await pause(120); // lets loading states show while there is no network
  return sample();
}

export const api = {
  /** GET /api/organization -> OrgSummary */
  organization: () => call<OrgSummary>('/api/organization', () => mock.organization()),

  /** GET /api/teams/{teamId} -> TeamDetail */
  team: (teamId: string) => call<TeamDetail>(`/api/teams/${encodeURIComponent(teamId)}`, () => mock.team(teamId)),

  /** GET /api/employees/{employeeId} -> EmployeeDetail */
  employee: (employeeId: string) =>
    call<EmployeeDetail>(`/api/employees/${encodeURIComponent(employeeId)}`, () => mock.employee(employeeId)),

  /** POST /api/employees/{employeeId}/reviews  body: { outcome, note } -> ReviewRecord */
  submitReview: (input: ReviewInput) =>
    call<ReviewRecord>(
      `/api/employees/${encodeURIComponent(input.employeeId)}/reviews`,
      () => mock.addReview(input),
      { method: 'POST', body: JSON.stringify({ outcome: input.outcome, note: input.note }) },
    ),
};
