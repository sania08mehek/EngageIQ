# EngageIQ — FindDataset Report
## Dataset Discovery, Mapping & Merge Documentation

---

## 1. Required Fields for PACE Framework

Before sourcing any external dataset, we documented exactly which fields the PACE scoring engine requires. The PACE framework operates on a **dual-layer, 9-metric model** that needs the following normalized [0, 1] inputs:

### Signal Layer — Employee Health Score (EHS)

| # | Required Field | Description | What It Measures |
|---|---------------|-------------|-----------------|
| 1 | `meeting_load` | Fraction of work hours spent in meetings | Calendar overload and time fragmentation |
| 2 | `focus_gap` | 1 − (longest uninterrupted block / work hours) | Inability to achieve deep work |
| 3 | `response_latency` | Normalized communication response delay | Communication burden / reactiveness |
| 4 | `after_hours_ratio` | After-hours events / total events | Work-life boundary erosion |

### Output Layer — Output Productivity Index (OPI)

| # | Required Field | Description | What It Measures |
|---|---------------|-------------|-----------------|
| 5 | `completion_rate` | Completed tasks / total assigned tasks | Task throughput |
| 6 | `velocity` | Normalized completed story points per sprint | Sprint delivery pace |
| 7 | `deadline_adherence` | On-time tasks / completed tasks | Timeliness of delivery |
| 8 | `code_activity` | Normalized code contribution index | Active development output |
| 9 | `rework_ratio` | Reopened or revised tasks / total tasks | Quality deficit / waste |

### Additional Fields for SPACE Comparison

For the framework comparison study, we also needed SPACE-compatible metrics:

| # | Required Field | SPACE Dimension | Description |
|---|---------------|----------------|-------------|
| 10 | `satisfaction_score` | S — Satisfaction | Employee satisfaction / well-being |
| 11 | `performance_score_space` | P — Performance | Blended outcome performance |
| 12 | `activity_score` | A — Activity | Volume of development actions |
| 13 | `communication_score` | C — Communication | Collaboration and knowledge sharing |
| 14 | `efficiency_score` | E — Efficiency | Flow state and productive coding time |

### Metadata Fields

| # | Required Field | Description |
|---|---------------|-------------|
| 15 | `employee_id` | Unique identifier |
| 16 | `employee_name` | Display name |
| 17 | `team` | Department / team assignment |
| 18 | `role` | Job title / role for normalization |

---

## 2. Source Datasets Used

### Dataset 1: AI Developer Productivity & Performance Dataset

| Property | Value |
|----------|-------|
| **Filename** | `ai_developer_productivity.csv` |
| **Source** | Kaggle |
| **Records** | 1,000 rows (daily records for 100 unique developers) |
| **Columns** | 12 |
| **Date Range** | Jan–Mar 2026 |
| **Data Type** | Synthetic / simulated developer behavioral data |

**Columns:**

| Column | Type | Range | Description |
|--------|------|-------|-------------|
| `Developer_ID` | String | DEV-101 to DEV-200 | Unique developer identifier |
| `Date` | Date | 2026-01-01 to 2026-03-31 | Record date |
| `Hours_Coding` | Float | 2.0 – 8.0 | Daily coding hours |
| `AI_Usage_Hours` | Float | 0.5 – 8.0 | Hours using AI tools |
| `Lines_of_Code` | Int | 132 – 1,450 | Lines produced per day |
| `Commits` | Int | 0 – 9 | Daily git commits |
| `Bugs_Reported` | Int | 0 – 20 | Bugs found/reported |
| `Sleep_Hours` | Float | 3.0 – 9.0 | Self-reported sleep hours |
| `Distractions` | Int | 0 – 10 | Daily distraction count |
| `Cognitive_Load` | Int | 2 – 10 | Perceived cognitive load (Likert) |
| `Stress_Level` | Int | 2 – 10 | Perceived stress (Likert) |
| `Task_Success` | Binary | 0 or 1 | Whether daily task was completed |

**Key statistics:**
- Mean coding hours: 4.99h, mean commits: 3.56/day
- Task success rate: 47.2% (fairly balanced binary outcome)
- 100 unique developers with 3–17 records each (mean: 10)

**Relevance to PACE:** Provides direct code activity metrics (commits, LOC), quality signals (bugs = rework proxy), well-being indicators (sleep, stress, cognitive load), and focus-time data (distractions, coding hours).

---

### Dataset 2: Extended Employee Performance and Productivity Data

| Property | Value |
|----------|-------|
| **Filename** | `Extended_Employee_Performance_and_Productivity_Data.csv` |
| **Source** | Kaggle |
| **Records** | 100,000 rows |
| **Columns** | 20 |
| **Data Type** | Synthetic HR analytics data |

**Columns:**

| Column | Type | Range | Description |
|--------|------|-------|-------------|
| `Employee_ID` | Int | 1 – 100,000 | Unique identifier |
| `Department` | Categorical | 9 departments | Engineering, IT, Finance, etc. |
| `Gender` | Categorical | Male/Female | Gender |
| `Age` | Int | 22 – 60 | Employee age |
| `Job_Title` | Categorical | 7 titles | Engineer, Developer, Manager, etc. |
| `Hire_Date` | Datetime | 2014 – 2024 | Date of hiring |
| `Years_At_Company` | Int | 0 – 10 | Tenure |
| `Education_Level` | Categorical | 3 levels | High School, Bachelor, etc. |
| `Performance_Score` | Int | 1 – 5 | Manager-rated performance (Likert) |
| `Monthly_Salary` | Float | 3,850 – 9,000 | Monthly salary |
| `Work_Hours_Per_Week` | Int | 30 – 60 | Weekly work hours |
| `Projects_Handled` | Int | 0 – 49 | Projects managed |
| `Overtime_Hours` | Int | 0 – 29 | Weekly overtime |
| `Sick_Days` | Int | 0 – 14 | Annual sick days taken |
| `Remote_Work_Frequency` | Int | 0 – 100 | % remote work |
| `Team_Size` | Int | 1 – 19 | Team members |
| `Training_Hours` | Int | 0 – 99 | Training hours completed |
| `Promotions` | Int | 0 – 2 | Number of promotions |
| `Employee_Satisfaction_Score` | Float | 1.0 – 5.0 | Self-reported satisfaction |
| `Resigned` | Boolean | True/False | Whether employee resigned |

**Key statistics:**
- Mean work hours: 44.96h/week, mean overtime: 14.51h
- Mean performance score: 3.0/5.0, mean satisfaction: 3.0/5.0
- 9 departments, 7 job titles — evenly distributed
- Mean projects handled: 24.4 (wide range 0–49)

**Relevance to PACE:** Provides work hours (meeting load proxy), overtime (after-hours proxy), performance scores (completion/velocity proxy), projects handled (velocity proxy), satisfaction (SPACE S-dimension), department and role information for normalization.

---

## 3. How Datasets Were Mapped and Merged

### 3.1 Merge Strategy Overview

Since neither dataset alone contains all 9 PACE input fields, we designed a **complementary merge** strategy:

```
AI Developer Dataset ──────────────┐
(Code metrics, well-being,         │     ┌─────────────────────────────┐
 focus/distraction data)           ├────►│    MERGED PACE DATASET      │
                                   │     │    500 employees             │
Extended Employee Dataset ─────────┘     │    37 columns               │
(Work hours, overtime,                   │    9 PACE + 6 SPACE features│
 performance, satisfaction)              └─────────────────────────────┘
```

### 3.2 Step-by-Step Merge Process

#### Step 1: Aggregate AI Developer Data

The AI dataset has multiple daily records per developer (3–17 rows each). We aggregated to one row per developer:

| Aggregation | Method | Result |
|-------------|--------|--------|
| `hours_coding_mean` | Mean of `Hours_Coding` | Average daily coding hours |
| `commits_total` / `commits_mean` | Sum / Mean of `Commits` | Cumulative and average commits |
| `bugs_reported_mean` | Mean of `Bugs_Reported` | Average daily bugs |
| `sleep_hours_mean` | Mean of `Sleep_Hours` | Average sleep quality |
| `distractions_mean` | Mean of `Distractions` | Average distraction level |
| `cognitive_load_mean` | Mean of `Cognitive_Load` | Average cognitive burden |
| `stress_level_mean` | Mean of `Stress_Level` | Average stress |
| `task_success_rate` | Mean of `Task_Success` | Proportion of successful tasks |

Result: 100 unique developer profiles.

#### Step 2: Sample from Employee Dataset

We randomly sampled 500 employees (with seed=42 for reproducibility) from the 100,000-record Employee dataset to get a diverse but manageable cohort.

#### Step 3: Cyclic Assignment

Each of the 500 sampled employees was assigned an AI developer profile by cycling through the 100 aggregated profiles (employee index mod 100). This ensures every employee gets code-level and well-being data.

#### Step 4: Field Mapping

The critical mapping step transforms source fields into PACE-compatible features:

### 3.3 Detailed Field Mapping Table

| PACE Target Field | Source Dataset(s) | Source Fields Used | Mapping Formula | Rationale |
|------------------|-------------------|-------------------|-----------------|-----------|
| **meeting_load** | Employee | `Work_Hours_Per_Week`, `Overtime_Hours` | `clip((WHpW × 0.30 + OT × 0.4) / 40, 0, 1)` | ~30% of work hours estimated as meetings; overtime adds meeting pressure. Max 40h used as ceiling. |
| **focus_gap** | AI Developer | `Distractions` (0–10 scale) | `clip(Distractions / 10, 0, 1)` | Higher distractions directly translate to focus fragmentation. Scale 0–10 maps naturally to 0–1. |
| **response_latency** | Both | `Team_Size` (Emp), `Hours_Coding` (AI) | `clip((TeamSize/20 × 0.5) + ((1 - CodingHrs/8) × 0.5), 0, 1)` | Larger teams = more communication overhead. Less coding time = more time spent responding. |
| **after_hours_ratio** | Employee | `Overtime_Hours` (0–29) | `clip(OT / 30, 0, 1)` | Overtime directly measures after-hours work. 30h as maximum normalization cap. |
| **completion_rate** | Both | `Task_Success` (AI), `Performance_Score` (Emp) | `clip(TaskSuccess × 0.6 + PerfScore/5 × 0.4, 0, 1)` | Blends actual task completion (60%) with manager-rated performance (40%) for a holistic completion view. |
| **velocity** | Both | `Projects_Handled` (Emp), `Commits` (AI) | `clip((Projects/50 × 0.5) + (Commits/9 × 0.5), 0, 1)` | Combines project throughput with code velocity for a comprehensive delivery pace measure. |
| **deadline_adherence** | Both | `Performance_Score` (Emp), `Sick_Days` (Emp) | `clip((PerfScore/5 × 0.6) + ((1 - SickDays/15) × 0.4), 0, 1)` | Higher performance implies better deadline meeting; fewer sick days = more consistent availability. |
| **code_activity** | AI Developer | `Commits`, `Lines_of_Code`, `Hours_Coding` | `clip((Commits/9 × 0.4) + (LOC/1500 × 0.3) + (CodingHrs/8 × 0.3), 0, 1)` | Multi-signal code activity combining commit frequency, output volume, and coding effort. |
| **rework_ratio** | AI Developer | `Bugs_Reported`, `Commits` | `clip((Bugs / (Commits + 1)) / P95, 0, 1)` | Bug-to-commit ratio as quality proxy. Normalized against 95th percentile to avoid outlier dominance. |

### 3.4 SPACE-Specific Mappings

| SPACE Dimension | Source Fields | Mapping Formula |
|----------------|---------------|-----------------|
| **S – Satisfaction** | `Employee_Satisfaction_Score` (1–5) | `Score / 5.0` |
| **P – Performance** | `Task_Success`, `Performance_Score`, `deadline_adherence` | `TaskSuccess × 0.4 + PerfScore/5 × 0.3 + Deadline × 0.3` |
| **A – Activity** | `Commits`, `Lines_of_Code`, `Projects_Handled` | `Commits/9 × 0.3 + LOC/1500 × 0.3 + Projects/50 × 0.4` |
| **C – Communication** | `response_latency`, `Training_Hours`, `Promotions` | `(1-Latency) × 0.5 + Training/100 × 0.3 + Promos/2 × 0.2` |
| **E – Efficiency** | `Hours_Coding`, `Distractions`, `Task_Success` | `CodingHrs/8 × 0.4 + (1-Distractions/10) × 0.3 + TaskSuccess × 0.3` |

---

## 4. Final Merged Dataset Summary

| Property | Value |
|----------|-------|
| **Total Records** | 500 employees |
| **Total Columns** | 37 |
| **PACE Feature Columns** | 9 (all normalized [0, 1]) |
| **SPACE Feature Columns** | 6 (all normalized [0, 1]) |
| **Metadata Columns** | 4 (employee_id, name, team, role) |
| **Raw Source Columns Retained** | 18 (for auditability) |
| **Output File** | `dataset/output/merged_dataset_full.csv` |
| **PACE-Ready File** | `dataset/pace_ready_merged.csv` |

### Train / Validate / Test Split

| Split | Records | Percentage | File |
|-------|---------|-----------|------|
| **Train** | 350 | 70% | `dataset/output/train_split.csv` |
| **Validate** | 75 | 15% | `dataset/output/validate_split.csv` |
| **Test** | 75 | 15% | `dataset/output/test_split.csv` |

Split performed with `random_state=42` for full reproducibility.

### Feature Statistics (Full Dataset, N=500)

| Feature | Mean | Std Dev | Min | Max |
|---------|------|---------|-----|-----|
| meeting_load | 0.482 | 0.110 | 0.240 | 0.740 |
| focus_gap | 0.414 | 0.093 | 0.223 | 0.650 |
| response_latency | 0.445 | 0.138 | 0.169 | 0.704 |
| after_hours_ratio | 0.478 | 0.291 | 0.000 | 0.967 |
| completion_rate | 0.516 | 0.155 | 0.080 | 0.920 |
| velocity | 0.421 | 0.155 | 0.102 | 0.749 |
| deadline_adherence | 0.556 | 0.203 | 0.147 | 1.000 |
| code_activity | 0.472 | 0.047 | 0.336 | 0.558 |
| rework_ratio | 0.622 | 0.188 | 0.309 | 1.000 |

> [!NOTE]
> All features show realistic distributions with reasonable variance, confirming the mapping produced a diverse and usable dataset. No features are degenerate (zero variance) or clipped at boundaries for more than a few records.

---

## 5. Limitations & Assumptions

1. **Cyclic AI profile assignment:** Each AI developer profile is reused 5 times across 500 employees. This means code metrics repeat cyclically — in a production scenario, each employee would have their own unique code metrics.

2. **Meeting hours estimation:** The 30% meeting-time assumption is an average. Real organizations vary significantly (some roles have 50%+ meetings).

3. **Both source datasets are synthetic:** Neither dataset contains real employee data. However, their statistical distributions are designed to mimic realistic workplace patterns.

4. **Rework normalization:** Using the 95th percentile as the normalization cap means that extreme rework ratios get clipped to 1.0, losing granularity at the high end.

5. **SPACE satisfaction is direct; PACE well-being is indirect:** The Employee Satisfaction Score maps directly to SPACE's Satisfaction dimension but is not used in PACE's EHS (by design — PACE avoids subjective survey data).
