# EngageIQ: Phase 2A & Phase 2B Test Run & Verification Guide

This guide provides instructions to run, verify, and test the unified **Phase 2A & 2B** implementation of EngageIQ.

---

## 1. Architecture Unification Summary

All modular pipeline components from `data_pipeline/` have been integrated into `engageiq-backend/`:

| Module | Location in `engageiq-backend/` | Purpose |
| :--- | :--- | :--- |
| **Configuration** | [`config.py`](file:///c:/Users/Irfan%20IR/Documents/IR%20Projects/EngageIQ/engageiq-backend/config.py) | Central weights (`EHS=0.40`, `OPI=0.60`), thresholds, paths, SQLite URL. |
| **Preprocessing** | [`preprocessing/`](file:///c:/Users/Irfan%20IR/Documents/IR%20Projects/EngageIQ/engageiq-backend/preprocessing) | `DataValidator`, `DataCleaner` (median imputation), `RoleAwareNormalizer`. |
| **Scoring Engine** | [`scoring/`](file:///c:/Users/Irfan%20IR/Documents/IR%20Projects/EngageIQ/engageiq-backend/scoring) | `EHS_Calculator` (40%), `OPI_Calculator` (60%), `PACEEngine`, `PatternDetector`. |
| **Database & DAO** | [`database/`](file:///c:/Users/Irfan%20IR/Documents/IR%20Projects/EngageIQ/engageiq-backend/database) | Relational SQLAlchemy models, `db_session.py`, `PipelineRepository`. |
| **Connectors & Webhooks** | [`integration/`](file:///c:/Users/Irfan%20IR/Documents/IR%20Projects/EngageIQ/engageiq-backend/integration) | GitHub, Slack, Jira, Calendar connectors, `IdentityResolver`, `MetricsAggregator`, `SyntheticRawEventsGenerator`, `webhook_router.py`. |
| **FastAPI Server** | [`main.py`](file:///c:/Users/Irfan%20IR/Documents/IR%20Projects/EngageIQ/engageiq-backend/main.py) | Unified API serving real REST endpoints (`/api/organization`, `/api/teams/*`, `/api/employees/*`, `/api/integration/*`, `/api/upload`). |
| **Integrations UI** | [`Integrations.tsx`](file:///c:/Users/Irfan%20IR/Documents/IR%20Projects/EngageIQ/engageiq-frontend/src/pages/Integrations.tsx) | Live dashboard page for connector health, identity resolution, webhook simulation, and manual/synthetic sync triggers. |

> [!NOTE]
> The temporary folder `data_pipeline/` has been cleared after migrating all modules, tests, datasets, and documentation.

---

## 2. Quick-Start: How to Launch the Stack

Open two separate PowerShell or Terminal windows:

### Terminal 1: Launch the Backend (FastAPI PACE Engine)
```powershell
cd "c:\Users\Irfan IR\Documents\IR Projects\EngageIQ\engageiq-backend"
.\venv\Scripts\uvicorn.exe main:app --reload --host 127.0.0.1 --port 8000
```
- **Health check URL:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Terminal 2: Launch the Frontend (React + Vite)
```powershell
cd "c:\Users\Irfan IR\Documents\IR Projects\EngageIQ\engageiq-frontend"
npm run dev
```
- **Dashboard URL:** [http://localhost:5173/](http://localhost:5173/)

---

## 3. Step-by-Step Test Run & Verification Walkthrough

Follow these 6 steps in your browser to verify that all mock dependencies and placeholders have been eliminated and live data persists to SQLite:

### Step 1: Home & Principles
1. Open [http://localhost:5173/](http://localhost:5173/).
2. Notice the navigation bar: **Overview**, **Dashboard**, **Integrations**, **PACE Simulator**.
3. All buttons are cleaned of "try" or "sample" tags. Click **View Dashboard** or **Data Connectors**.

### Step 2: Data Sources & Telemetry Integrations (`/integrations`)
1. Click **Integrations** in the top navigation.
2. **Connector Cards Grid:** Inspect the 5 cards:
   - **GitHub**: Code activity volume, PR reviews, code churn.
   - **Jira Software**: Sprint velocity, task completion rate, deadline adherence.
   - **Slack**: Mention response latency (min), after-hours activity.
   - **Google Calendar**: Meeting hours, focus gap blocks.
   - **CSV Ingestion Pipeline**: Direct batch upload.
3. **Tab 1: Sync Trigger**:
   - Click **⚡ Run Multi-Source Sync** in the top header.
   - This invokes `POST /api/integration/run-aggregation`, triggering the `SyntheticRawEventsGenerator` for all mapped employees, aggregating payloads through `MetricsAggregator`, computing 40:60 PACE scores, detecting risk patterns, and persisting records into `engageiq.db`.
   - A green banner confirms successful synchronization.
4. **Tab 2: Identity Resolver Directory**:
   - Click the **Identity Resolver Directory** tab.
   - Verify the table showing employees (Sarah Connor, Alex Rivera, Elena Rostova, Marcus Vance, Jordan Patel) mapped across their Slack IDs, Jira UUIDs, GitHub usernames, work emails, and local timezones.
5. **Tab 3: Webhook Receiver Test Console**:
   - Click the **Webhook Receiver Test Console** tab.
   - Select **GITHUB**, **SLACK**, or **JIRA**.
   - Click **Dispatch Webhook**.
   - Inspect the live HTTP 200 JSON acknowledgment returned by the FastAPI webhook receiver.

### Step 3: Organization Dashboard (`/dashboard`)
1. Click **Dashboard** in the top navigation.
2. Verify:
   - **12-Week Organization Trend Chart** renders without any "Coming Soon" blur or overlay.
   - **Org KPI Stats**: Real Composite PACE, Work-pattern health (EHS), Output deliverables (OPI), and Risk distribution.
   - **Teams Table**: Real team breakdown with sparklines, risk badges, and headcount.
   - **Review Queue**: Flagged employees in need of contextual manager review.

### Step 4: CSV Data Ingestion Test
1. On the Dashboard or Integrations page, click **Upload CSV Data** (or **Upload CSV File**).
2. Drag and drop or browse to select:
   `c:\Users\Irfan IR\Documents\IR Projects\EngageIQ\engageiq-backend\sample_data.csv`
3. Click **Upload & Process Data**.
4. The backend runs the 5-step pipeline:
   - Schema validation
   - Cleaner & median imputation
   - Role-aware normalization
   - EHS & OPI 40:60 PACE scoring
   - Persists all 50 records and risk events to SQLite.
5. Click **View Dashboard** to see the newly updated metrics!

### Step 5: Team & Employee Drill-Down
1. From the Dashboard, click any team (e.g. **Platform Engineering** or **Core Platform**).
2. Verify **Team Trend Chart** and **Team Members Table** render cleanly.
3. Click any employee (e.g. **Sarah Connor** or an engineer from `sample_data.csv`).
4. On the Employee detail screen:
   - Verify the **12-week individual trajectory chart** with the dashed baseline.
   - Verify both **Feature Tables**:
     - *How work happens (EHS · 40%)*: Meeting Load, Focus Gaps, Response Latency, After-Hours.
     - *What is delivered (OPI · 60%)*: Task Completion, Sprint Velocity, Deadline Adherence, Code Activity, Rework Churn.
   - Verify **Pattern Insights** and **Contributing Signals**.

### Step 6: Human-in-the-Loop Manager Review
1. On the Employee detail view, scroll down to the **Review Panel** on the right side.
2. Select a decision outcome: e.g. **Monitor trend** or **Discuss workload**.
3. Enter a contextual review note: e.g. *"Discussed workload during 1:1; rebalancing sprint tasks."*
4. Click **Save Review**.
5. Verify the review is saved to SQLite and appears immediately in the employee's historical review log.

---

## 4. Backend CLI Tools & Test Suite

You can also run the pipeline or integration CLI tools directly from PowerShell:

```powershell
cd "c:\Users\Irfan IR\Documents\IR Projects\EngageIQ\engageiq-backend"

# 1. Run the CSV Data Pipeline CLI
.\venv\Scripts\python.exe run_pipeline.py --csv sample_data.csv

# 2. Run the Multi-Source SaaS Integration Pipeline CLI
.\venv\Scripts\python.exe run_integration.py

# 3. Run the automated Pytest Test Suite (19 passing unit tests)
.\venv\Scripts\pytest.exe
```
