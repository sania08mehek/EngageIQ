# EngageIQ (PACE) — Detailed Build Plan

Based on the **EngageIQ Architecture Document** and **Algorithm Details**, this build plan is structured into 4 distinct phases. 

The first two phases focus on establishing the core processing engine (without machine learning) and visualizing the PACE scores using mock/sample data ingested via CSV uploads from the frontend. Phases 3 and 4 evolve the system into a production-ready, fully automated, and ML-powered platform.

---

## Phase 1: Foundation (Data Structure & File Handling)
**Goal:** Set up the backend, define the data models, and implement the CSV ingestion pipeline from the React frontend.

1. **Backend Initialization**
   - Initialize a Python FastAPI project (`engageiq-backend`).
   - Setup a SQLite database for MVP persistence.
   - Define SQLAlchemy models matching the proposed architecture: `Employee`, `SignalMetrics`, `OutputMetrics`, `PaceScores`, and `RiskEvents`.

2. **File Ingestion API (No ML)**
   - Create a `/api/upload` endpoint in FastAPI to accept CSV files containing historical work metadata (meetings, Jira tasks, commits, messages).
   - Implement the `Data Processing` step to parse CSV rows, normalize the data, and store raw events in the SQLite database.

3. **Frontend Tweaks & Upload UI**
   - Update the existing React/Vite frontend (`engageiq-frontend`).
   - Create a dedicated "Data Ingestion" UI component to allow managers to upload CSV files.
   - Establish API connections via Axios/Fetch to communicate with the FastAPI backend.

---

## Phase 2: Core Processing Logic & Dashboard (Without ML)
**Goal:** Implement the mathematical EHS and OPI algorithms, calculate PACE scores, and visualize them on the dashboard.

1. **PACE Scoring Engine (Backend)**
   - **EHS Algorithm:** Calculate meeting load, focus gap, response latency, and after-hours ratio using a linear formula.
   - **OPI Algorithm:** Calculate task completion, sprint velocity, deadline adherence, code activity, and rework ratio.
   - **PACE Fusion:** Apply the `(0.4 * EHS) + (0.6 * OPI)` weightings to generate the final scores.

2. **Statistical Trend & Anomaly Detection**
   - Implement the rolling baseline standard deviation approach (no ML) to flag sudden changes or persistent deteriorations in employee performance.
   - Implement the **Risk Classification Module** to categorize employees into *Healthy*, *Moderate*, or *At-Risk*.

3. **Dashboard Visualization (Frontend)**
   - Build out the Manager Dashboard to visualize the organization and team views.
   - Implement charts (using libraries like Recharts or Chart.js) for PACE distributions, team-level trends, and EHS vs OPI comparisons.
   - Add detailed drill-downs for employees, showing the explanations for their Risk Band and score trajectory.

---

## Phase 3: Automated Data Ingestion & ML Pipeline
**Goal:** Connect to live SaaS tools and introduce machine learning for trend detection.

1. **API Connectors & Integrations**
   - Replace manual CSV uploads with automated integrations (OAuth + REST API).
   - Implement connectors for **Google Calendar/Outlook** (for EHS) and **Jira/GitHub** (for OPI).
   - Setup cron jobs/schedulers to fetch data incrementally.

2. **Machine Learning Trend Detection**
   - Transition from simple statistical anomaly detection to an LSTM-based time-series model to identify complex patterns in worker burnout and productivity drops.
   - Serve the ML model via the FastAPI backend to generate intelligent Risk Signals.

3. **Advanced UI Connections**
   - Build an Integrations Settings page for OAuth connections.
   - Update charts to reflect predictive ML trends and richer data over longer timelines.

---

## Phase 4: Human-in-the-Loop, Polish & Production
**Goal:** Finalize the Responsible AI workflows, add role-based access, and prepare for production deployment.

1. **Human Review Workflow**
   - Implement the "Contextual Decision" workflow. Managers will receive alerts for At-Risk employees and must provide contextual feedback (e.g., "Overriding automated risk – employee is on a special project").
   
2. **Privacy, Governance & RBAC**
   - Implement Role-Based Access Control (RBAC) (Admin, Manager, Employee).
   - Ensure Employees can only see their own scores, while Managers can see aggregated team data and their direct reports.

3. **Productionization**
   - Migrate from SQLite to PostgreSQL.
   - Containerize both Frontend and Backend using Docker.
   - Polish the UI with rich aesthetics, glassmorphism, dynamic animations, and high-quality UX suitable for a modern SaaS product.
