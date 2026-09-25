# EngageIQ frontend

React + TypeScript frontend for EngageIQ / PACE. It runs today on built-in sample data, so you can build and demo the UI before the FastAPI backend exists.

## Run it

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # type-check and production build
```

## Pages

| Route | What it is |
|---|---|
| `/` | Overview: the dual-lens idea, the pipeline, the privacy boundary, the risk bands |
| `/dashboard` | Organization view: PACE, EHS and OPI trend, risk mix, teams, review queue |
| `/dashboard/teams/:teamId` | Team view: team trend, people table, comparison with 4 weeks ago |
| `/dashboard/people/:employeeId` | Employee view: trend against their own baseline, role-aware measures, explanation, human review form and history |
| `/pace-score` | PACE score calculator: adjust readings, see EHS, OPI and PACE, then check a 4-week window for patterns |

## Connect the backend later

All data goes through `src/api/client.ts`. Nothing else in the app knows where data comes from.

1. Copy `.env.example` to `.env` and set `VITE_API_URL=http://localhost:8000`.
2. Return these shapes (defined in `src/api/types.ts`) from FastAPI:

| Endpoint | Returns |
|---|---|
| `GET /api/organization` | `OrgSummary` |
| `GET /api/teams/{teamId}` | `TeamDetail` |
| `GET /api/employees/{employeeId}` | `EmployeeDetail` |
| `POST /api/employees/{employeeId}/reviews` with `{ outcome, note }` | `ReviewRecord` |

3. Enable CORS on FastAPI for `http://localhost:5173`, or uncomment the proxy in `vite.config.ts`.

The types map to the tables in the architecture doc: `pace_scores` feed `history`, `signal_metrics` and `output_metrics` feed `features`, and `risk_events` feed the review queue and `reviews`.

## Where the logic lives

| File | Purpose |
|---|---|
| `src/lib/pace.ts` | `PACE = 0.4 x EHS + 0.6 x OPI`, the 0.40 and 0.70 bands, and the simple trend and pattern detection. Replace `detectPatterns` with the backend's anomaly output when it exists. |
| `src/lib/features.ts` | Calculator measures and presets. The way each reading becomes a 0 to 1 value is a placeholder until role-specific settings exist. |
| `src/api/mock.ts` | Sample data (16 people, 4 teams, 12 weeks). Delete it when the backend is live. |
| `src/styles.css` | Design tokens and all styling. |

## Design rules kept from the architecture doc

- Output weighs more than work patterns (60/40).
- Every flag comes with an explanation and a trend, never a bare score.
- Nothing is automatic. The review form is a core part of the employee page.
- No surveillance measures appear anywhere in the UI.
