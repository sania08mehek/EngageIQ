"""
EngageIQ - Dataset Merge, PACE vs SPACE Scoring Pipeline
=========================================================
This script:
1. Reads both source datasets
2. Maps and merges them into PACE-compatible format
3. Splits into train/validate/test
4. Scores with PACE framework
5. Scores with SPACE framework
6. Generates comparison metrics and exports results
"""

import pandas as pd
import numpy as np
import os
import json
from pathlib import Path

np.random.seed(42)

# ================================================================
# PATHS
# ================================================================
BASE = Path(__file__).resolve().parent
DATASET_DIR = BASE / "dataset"
OUTPUT_DIR = BASE / "dataset" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ================================================================
# STEP 1: LOAD SOURCE DATASETS
# ================================================================
print("=" * 70)
print("STEP 1: Loading source datasets")
print("=" * 70)

df_ai = pd.read_csv(DATASET_DIR / "ai_developer_productivity.csv")
df_emp = pd.read_csv(DATASET_DIR / "Extended_Employee_Performance_and_Productivity_Data.csv")

print(f"AI Developer Productivity: {df_ai.shape[0]} rows, {df_ai.shape[1]} cols")
print(f"Extended Employee Performance: {df_emp.shape[0]} rows, {df_emp.shape[1]} cols")

# ================================================================
# STEP 2: AGGREGATE AI DATASET (multiple rows per developer)
# ================================================================
print("\n" + "=" * 70)
print("STEP 2: Aggregating AI Developer dataset by Developer_ID")
print("=" * 70)

df_ai_agg = df_ai.groupby("Developer_ID").agg(
    hours_coding_mean=("Hours_Coding", "mean"),
    ai_usage_hours_mean=("AI_Usage_Hours", "mean"),
    lines_of_code_mean=("Lines_of_Code", "mean"),
    commits_total=("Commits", "sum"),
    commits_mean=("Commits", "mean"),
    bugs_reported_total=("Bugs_Reported", "sum"),
    bugs_reported_mean=("Bugs_Reported", "mean"),
    sleep_hours_mean=("Sleep_Hours", "mean"),
    distractions_mean=("Distractions", "mean"),
    cognitive_load_mean=("Cognitive_Load", "mean"),
    stress_level_mean=("Stress_Level", "mean"),
    task_success_rate=("Task_Success", "mean"),
    record_count=("Task_Success", "count"),
).reset_index()

print(f"Aggregated AI developers: {df_ai_agg.shape[0]} unique developers")
print(f"Records per developer: min={df_ai_agg['record_count'].min()}, max={df_ai_agg['record_count'].max()}, mean={df_ai_agg['record_count'].mean():.1f}")

# ================================================================
# STEP 3: SAMPLE & MAP FROM EMPLOYEE DATASET
# ================================================================
print("\n" + "=" * 70)
print("STEP 3: Sampling from Employee dataset & mapping fields")
print("=" * 70)

# We want to build employees that have BOTH Signal Layer and Output Layer data
# Strategy: Take 500 employees from Employee dataset, enrich with AI-developer
# data by cycling through the 100 AI developers

# Sample 500 employees (diverse departments and roles)
df_emp_sample = df_emp.sample(n=500, random_state=42).reset_index(drop=True)
print(f"Sampled {len(df_emp_sample)} employees from Extended dataset")

# Assign each sampled employee an AI developer profile (cycle through 100)
ai_ids = df_ai_agg["Developer_ID"].values
df_emp_sample["ai_match_idx"] = [i % len(ai_ids) for i in range(len(df_emp_sample))]
df_emp_sample = df_emp_sample.merge(
    df_ai_agg.reset_index(drop=True).rename(columns={"Developer_ID": "ai_dev_id"}),
    left_on="ai_match_idx",
    right_index=True,
    how="left"
)

# ================================================================
# STEP 4: BUILD PACE-COMPATIBLE FEATURES (FIELD MAPPING)
# ================================================================
print("\n" + "=" * 70)
print("STEP 4: Mapping source fields to PACE features")
print("=" * 70)

# --- SIGNAL LAYER (EHS) ---
# meeting_load: Derived from Work_Hours_Per_Week
#   Higher work hours + overtime = more meeting/work load
#   Assumption: ~30% of work hours are meetings, plus overtime increases load
meeting_hours_est = df_emp_sample["Work_Hours_Per_Week"] * 0.30 + df_emp_sample["Overtime_Hours"] * 0.4
max_meeting_hours = 40  # reasonable maximum
df_emp_sample["meeting_load"] = np.clip(meeting_hours_est / max_meeting_hours, 0, 1)

# focus_gap: Derived from Distractions (AI dataset, scale 0-10)
#   More distractions = less focus time = higher focus gap
df_emp_sample["focus_gap"] = np.clip(df_emp_sample["distractions_mean"] / 10.0, 0, 1)

# response_latency: Derived from inverse of AI_Usage_Hours + Work_Hours ratio
#   Employees with more hours but lower AI usage may have slower workflows
#   Also influenced by team size (larger teams = more communication overhead)
latency_proxy = (df_emp_sample["Team_Size"] / 20.0) * 0.5 + (1 - df_emp_sample["hours_coding_mean"] / 8.0) * 0.5
df_emp_sample["response_latency"] = np.clip(latency_proxy, 0, 1)

# after_hours_ratio: Derived from Overtime_Hours relative to standard 40h week
df_emp_sample["after_hours_ratio"] = np.clip(df_emp_sample["Overtime_Hours"] / 30.0, 0, 1)

# --- OUTPUT LAYER (OPI) ---
# completion_rate: Derived from task_success_rate (AI) + Performance_Score (Emp)
#   Blend both sources - actual task completion + performance rating
completion_blend = (df_emp_sample["task_success_rate"] * 0.6 + 
                    df_emp_sample["Performance_Score"] / 5.0 * 0.4)
df_emp_sample["completion_rate"] = np.clip(completion_blend, 0, 1)

# velocity: Derived from Projects_Handled normalized + commits_mean
velocity_proxy = (df_emp_sample["Projects_Handled"] / 50.0) * 0.5 + \
                 (df_emp_sample["commits_mean"] / 9.0) * 0.5
df_emp_sample["velocity"] = np.clip(velocity_proxy, 0, 1)

# deadline_adherence: Derived from Performance_Score + inverse of Sick_Days
#   Higher performance & fewer sick days = better deadline adherence
deadline_proxy = (df_emp_sample["Performance_Score"] / 5.0) * 0.6 + \
                 (1 - df_emp_sample["Sick_Days"] / 15.0) * 0.4
df_emp_sample["deadline_adherence"] = np.clip(deadline_proxy, 0, 1)

# code_activity: Directly from commits + lines_of_code + coding hours
code_activity_proxy = (df_emp_sample["commits_mean"] / 9.0) * 0.4 + \
                      (df_emp_sample["lines_of_code_mean"] / 1500.0) * 0.3 + \
                      (df_emp_sample["hours_coding_mean"] / 8.0) * 0.3
df_emp_sample["code_activity"] = np.clip(code_activity_proxy, 0, 1)

# rework_ratio: Derived from bugs_reported / (lines_of_code as proxy for total work)
rework_proxy = df_emp_sample["bugs_reported_mean"] / (df_emp_sample["commits_mean"] + 1)
df_emp_sample["rework_ratio"] = np.clip(rework_proxy / rework_proxy.quantile(0.95), 0, 1)

# --- METADATA ---
df_emp_sample["employee_id"] = [f"EMP-{str(i+1).zfill(4)}" for i in range(len(df_emp_sample))]
df_emp_sample["employee_name"] = [f"Employee_{i+1}" for i in range(len(df_emp_sample))]
df_emp_sample["team"] = df_emp_sample["Department"]
df_emp_sample["role"] = df_emp_sample["Job_Title"]

# --- SPACE-SPECIFIC FIELDS ---
# Satisfaction: Employee_Satisfaction_Score (1-5 scale)
df_emp_sample["satisfaction_score"] = df_emp_sample["Employee_Satisfaction_Score"] / 5.0

# Communication: Inverse of response_latency + team_size influence
df_emp_sample["communication_score"] = np.clip(
    (1 - df_emp_sample["response_latency"]) * 0.5 + 
    (df_emp_sample["Training_Hours"] / 100.0) * 0.3 +
    (df_emp_sample["Promotions"] / 2.0) * 0.2, 0, 1
)

# Well-being: Sleep, stress, cognitive load from AI dataset
df_emp_sample["wellbeing_score"] = np.clip(
    (df_emp_sample["sleep_hours_mean"] / 9.0) * 0.4 +
    (1 - df_emp_sample["stress_level_mean"] / 10.0) * 0.3 +
    (1 - df_emp_sample["cognitive_load_mean"] / 10.0) * 0.3, 0, 1
)

# Efficiency/Flow: Hours_Coding / total work hours + inverse of distractions
df_emp_sample["efficiency_score"] = np.clip(
    (df_emp_sample["hours_coding_mean"] / 8.0) * 0.4 +
    (1 - df_emp_sample["distractions_mean"] / 10.0) * 0.3 +
    (df_emp_sample["task_success_rate"]) * 0.3, 0, 1
)

# Activity: Commits + lines of code + projects handled
df_emp_sample["activity_score"] = np.clip(
    (df_emp_sample["commits_mean"] / 9.0) * 0.3 +
    (df_emp_sample["lines_of_code_mean"] / 1500.0) * 0.3 +
    (df_emp_sample["Projects_Handled"] / 50.0) * 0.4, 0, 1
)

# Performance (SPACE): blended from task_success + performance_score + deadline
df_emp_sample["performance_score_space"] = np.clip(
    df_emp_sample["task_success_rate"] * 0.4 +
    df_emp_sample["Performance_Score"] / 5.0 * 0.3 +
    df_emp_sample["deadline_adherence"] * 0.3, 0, 1
)

print("Field mapping complete. Generated features:")
pace_features = ["meeting_load", "focus_gap", "response_latency", "after_hours_ratio",
                 "completion_rate", "velocity", "deadline_adherence", "code_activity", "rework_ratio"]
space_features = ["satisfaction_score", "performance_score_space", "activity_score",
                  "communication_score", "efficiency_score", "wellbeing_score"]
for f in pace_features:
    print(f"  PACE - {f}: mean={df_emp_sample[f].mean():.3f}, std={df_emp_sample[f].std():.3f}, "
          f"min={df_emp_sample[f].min():.3f}, max={df_emp_sample[f].max():.3f}")
for f in space_features:
    print(f"  SPACE - {f}: mean={df_emp_sample[f].mean():.3f}, std={df_emp_sample[f].std():.3f}, "
          f"min={df_emp_sample[f].min():.3f}, max={df_emp_sample[f].max():.3f}")

# ================================================================
# STEP 5: BUILD FINAL MERGED DATASET
# ================================================================
print("\n" + "=" * 70)
print("STEP 5: Building final merged dataset")
print("=" * 70)

# Select final columns
final_cols = ["employee_id", "employee_name", "team", "role"] + pace_features + space_features + \
             ["Employee_Satisfaction_Score", "Performance_Score", "Work_Hours_Per_Week",
              "Overtime_Hours", "Projects_Handled", "Sick_Days", "Remote_Work_Frequency",
              "Training_Hours", "Promotions", "stress_level_mean", "cognitive_load_mean",
              "sleep_hours_mean", "commits_mean", "bugs_reported_mean", "task_success_rate",
              "hours_coding_mean", "lines_of_code_mean", "distractions_mean"]

df_final = df_emp_sample[final_cols].copy()
print(f"Final merged dataset: {df_final.shape[0]} rows, {df_final.shape[1]} cols")

# Save full merged dataset
df_final.to_csv(OUTPUT_DIR / "merged_dataset_full.csv", index=False)
print(f"Saved: {OUTPUT_DIR / 'merged_dataset_full.csv'}")

# ================================================================
# STEP 6: TRAIN / VALIDATE / TEST SPLIT
# ================================================================
print("\n" + "=" * 70)
print("STEP 6: Splitting into Train / Validate / Test")
print("=" * 70)

# Shuffle
df_shuffled = df_final.sample(frac=1, random_state=42).reset_index(drop=True)
n = len(df_shuffled)

# 70% train, 15% validate, 15% test
train_end = int(n * 0.70)
val_end = int(n * 0.85)

df_train = df_shuffled.iloc[:train_end].reset_index(drop=True)
df_val = df_shuffled.iloc[train_end:val_end].reset_index(drop=True)
df_test = df_shuffled.iloc[val_end:].reset_index(drop=True)

df_train.to_csv(OUTPUT_DIR / "train_split.csv", index=False)
df_val.to_csv(OUTPUT_DIR / "validate_split.csv", index=False)
df_test.to_csv(OUTPUT_DIR / "test_split.csv", index=False)

print(f"Train: {len(df_train)} records ({len(df_train)/n*100:.1f}%)")
print(f"Validate: {len(df_val)} records ({len(df_val)/n*100:.1f}%)")
print(f"Test: {len(df_test)} records ({len(df_test)/n*100:.1f}%)")

# ================================================================
# STEP 7: PACE SCORING ENGINE
# ================================================================
print("\n" + "=" * 70)
print("STEP 7: Running PACE Framework Scoring")
print("=" * 70)

# PACE weights (from config.py)
W_EHS = 0.40
W_OPI = 0.60

# EHS weights
W_MEETING = 0.30
W_FOCUS = 0.30
W_LATENCY = 0.20
W_AFTERHOURS = 0.20

# OPI weights
W_COMPLETION = 0.25
W_VELOCITY = 0.25
W_DEADLINE = 0.20
W_ACTIVITY = 0.20
W_REWORK = 0.10

def compute_ehs(row):
    ehs = 1.0 - (W_MEETING * row["meeting_load"] +
                  W_FOCUS * row["focus_gap"] +
                  W_LATENCY * row["response_latency"] +
                  W_AFTERHOURS * row["after_hours_ratio"])
    return max(0.0, min(1.0, round(ehs, 4)))

def compute_opi(row):
    positive = (W_COMPLETION * row["completion_rate"] +
                W_VELOCITY * row["velocity"] +
                W_DEADLINE * row["deadline_adherence"] +
                W_ACTIVITY * row["code_activity"])
    penalty = W_REWORK * row["rework_ratio"]
    opi = positive - penalty
    return max(0.0, min(1.0, round(opi, 4)))

def compute_pace(ehs, opi):
    pace = W_EHS * ehs + W_OPI * opi
    return max(0.0, min(1.0, round(pace, 4)))

def classify_risk_pace(pace_score):
    if pace_score >= 0.70:
        return "Healthy"
    elif pace_score >= 0.40:
        return "Moderate"
    else:
        return "At-Risk"

# Apply PACE scoring to all splits
for name, df in [("train", df_train), ("validate", df_val), ("test", df_test)]:
    df["EHS"] = df.apply(compute_ehs, axis=1)
    df["OPI"] = df.apply(compute_opi, axis=1)
    df["PACE_Score"] = df.apply(lambda r: compute_pace(r["EHS"], r["OPI"]), axis=1)
    df["PACE_Risk_Band"] = df["PACE_Score"].apply(classify_risk_pace)
    
    print(f"\n{name.upper()} split PACE results:")
    print(f"  Mean EHS: {df['EHS'].mean():.4f} (std: {df['EHS'].std():.4f})")
    print(f"  Mean OPI: {df['OPI'].mean():.4f} (std: {df['OPI'].std():.4f})")
    print(f"  Mean PACE: {df['PACE_Score'].mean():.4f} (std: {df['PACE_Score'].std():.4f})")
    print(f"  Risk distribution: {dict(df['PACE_Risk_Band'].value_counts())}")

# ================================================================
# STEP 8: SPACE FRAMEWORK SCORING
# ================================================================
print("\n" + "=" * 70)
print("STEP 8: Running SPACE Framework Scoring")
print("=" * 70)

# SPACE scoring: pick 3+ dimensions (as recommended by SPACE authors)
# We use all 5 dimensions with equal weight (SPACE doesn't prescribe weights)
# Dimensions: Satisfaction, Performance, Activity, Communication, Efficiency
# SPACE does NOT produce a single score, but we compute a composite for comparison

# SPACE dimensional scores (already computed in Step 4)
# Method 1: Individual dimension reporting (SPACE's intended use)
# Method 2: Composite score for comparison (arithmetic mean of 5 dimensions)

SPACE_DIMS = {
    "S_Satisfaction": "satisfaction_score",
    "P_Performance": "performance_score_space",
    "A_Activity": "activity_score",
    "C_Communication": "communication_score",
    "E_Efficiency": "efficiency_score",
}

# SPACE doesn't specify weights, so we use equal weighting (1/5 each)
# This is the most neutral implementation possible
SPACE_WEIGHT = 1.0 / len(SPACE_DIMS)

def compute_space_composite(row):
    """Compute SPACE composite score as equal-weighted mean of 5 dimensions."""
    total = sum(row[col] for col in SPACE_DIMS.values())
    return round(total * SPACE_WEIGHT, 4)

def classify_risk_space(score):
    """Apply same risk thresholds for fair comparison."""
    if score >= 0.70:
        return "Healthy"
    elif score >= 0.40:
        return "Moderate"
    else:
        return "At-Risk"

for name, df in [("train", df_train), ("validate", df_val), ("test", df_test)]:
    # Individual dimension scores
    for dim_name, col in SPACE_DIMS.items():
        df[dim_name] = df[col]
    
    # Composite (for comparison purposes only - SPACE doesn't normally do this)
    df["SPACE_Composite"] = df.apply(compute_space_composite, axis=1)
    df["SPACE_Risk_Band"] = df["SPACE_Composite"].apply(classify_risk_space)
    
    print(f"\n{name.upper()} split SPACE results:")
    for dim_name, col in SPACE_DIMS.items():
        print(f"  {dim_name}: mean={df[dim_name].mean():.4f}, std={df[dim_name].std():.4f}")
    print(f"  SPACE Composite: {df['SPACE_Composite'].mean():.4f} (std: {df['SPACE_Composite'].std():.4f})")
    print(f"  Risk distribution: {dict(df['SPACE_Risk_Band'].value_counts())}")

# ================================================================
# STEP 9: COMPARISON ANALYSIS
# ================================================================
print("\n" + "=" * 70)
print("STEP 9: PACE vs SPACE Comparison Analysis")
print("=" * 70)

# Use test split for final comparison
df_compare = df_test.copy()

# --- Metric 1: Risk Band Agreement ---
agreement = (df_compare["PACE_Risk_Band"] == df_compare["SPACE_Risk_Band"]).mean()
print(f"\nRisk Band Agreement Rate: {agreement:.2%}")

# --- Metric 2: Cross-tabulation ---
crosstab = pd.crosstab(df_compare["PACE_Risk_Band"], df_compare["SPACE_Risk_Band"],
                       margins=True, margins_name="Total")
print("\nRisk Band Cross-Tabulation (PACE rows, SPACE columns):")
print(crosstab.to_string())

# --- Metric 3: Score Correlation ---
corr = df_compare["PACE_Score"].corr(df_compare["SPACE_Composite"])
print(f"\nPACE-SPACE Score Correlation (Pearson r): {corr:.4f}")

# --- Metric 4: Score Distribution Comparison ---
print("\nScore Distribution Comparison (Test Split):")
print(f"{'Metric':<30} {'PACE':>12} {'SPACE':>12} {'Difference':>12}")
print("-" * 66)
pace_mean = df_compare["PACE_Score"].mean()
space_mean = df_compare["SPACE_Composite"].mean()
print(f"{'Mean Score':<30} {pace_mean:>12.4f} {space_mean:>12.4f} {pace_mean-space_mean:>+12.4f}")

pace_std = df_compare["PACE_Score"].std()
space_std = df_compare["SPACE_Composite"].std()
print(f"{'Std Deviation':<30} {pace_std:>12.4f} {space_std:>12.4f} {pace_std-space_std:>+12.4f}")

pace_med = df_compare["PACE_Score"].median()
space_med = df_compare["SPACE_Composite"].median()
print(f"{'Median Score':<30} {pace_med:>12.4f} {space_med:>12.4f} {pace_med-space_med:>+12.4f}")

pace_min = df_compare["PACE_Score"].min()
space_min = df_compare["SPACE_Composite"].min()
print(f"{'Min Score':<30} {pace_min:>12.4f} {space_min:>12.4f} {pace_min-space_min:>+12.4f}")

pace_max = df_compare["PACE_Score"].max()
space_max = df_compare["SPACE_Composite"].max()
print(f"{'Max Score':<30} {pace_max:>12.4f} {space_max:>12.4f} {pace_max-space_max:>+12.4f}")

# --- Metric 5: Discriminative Power (Coefficient of Variation) ---
pace_cv = pace_std / pace_mean if pace_mean > 0 else 0
space_cv = space_std / space_mean if space_mean > 0 else 0
print(f"{'Coeff. of Variation':<30} {pace_cv:>12.4f} {space_cv:>12.4f} {pace_cv-space_cv:>+12.4f}")

# --- Metric 6: Risk Detection Rates ---
print("\nRisk Detection Comparison:")
for band in ["At-Risk", "Moderate", "Healthy"]:
    pace_count = (df_compare["PACE_Risk_Band"] == band).sum()
    space_count = (df_compare["SPACE_Risk_Band"] == band).sum()
    pace_pct = pace_count / len(df_compare) * 100
    space_pct = space_count / len(df_compare) * 100
    print(f"  {band:<12}: PACE = {pace_count:>4} ({pace_pct:5.1f}%)  |  SPACE = {space_count:>4} ({space_pct:5.1f}%)")

# --- Metric 7: Sensitivity Analysis ---
print("\nSensitivity Analysis (Partial Derivatives of PACE Score):")
pace_sensitivities = {
    "meeting_load": -0.40 * 0.30,
    "focus_gap": -0.40 * 0.30,
    "response_latency": -0.40 * 0.20,
    "after_hours_ratio": -0.40 * 0.20,
    "completion_rate": +0.60 * 0.25,
    "velocity": +0.60 * 0.25,
    "deadline_adherence": +0.60 * 0.20,
    "code_activity": +0.60 * 0.20,
    "rework_ratio": -0.60 * 0.10,
}
for metric, sensitivity in sorted(pace_sensitivities.items(), key=lambda x: abs(x[1]), reverse=True):
    print(f"  dPACE/d({metric}) = {sensitivity:+.3f}")

space_sensitivities = {dim: SPACE_WEIGHT for dim in SPACE_DIMS}
print("\nSPACE Dimension Sensitivities (Equal Weight):")
for dim, sensitivity in space_sensitivities.items():
    print(f"  dSPACE/d({dim}) = +{sensitivity:.3f}")

# --- Metric 8: Divergence Cases (where frameworks disagree most) ---
df_compare["score_diff"] = abs(df_compare["PACE_Score"] - df_compare["SPACE_Composite"])
df_compare["band_agree"] = df_compare["PACE_Risk_Band"] == df_compare["SPACE_Risk_Band"]

print(f"\nDivergence Analysis:")
print(f"  Mean absolute score difference: {df_compare['score_diff'].mean():.4f}")
print(f"  Max absolute score difference: {df_compare['score_diff'].max():.4f}")
print(f"  Cases where risk bands disagree: {(~df_compare['band_agree']).sum()} / {len(df_compare)} ({(~df_compare['band_agree']).mean():.1%})")

# Top 5 most divergent cases
print("\nTop 5 Most Divergent Cases:")
divergent = df_compare.nlargest(5, "score_diff")[
    ["employee_id", "PACE_Score", "PACE_Risk_Band", "SPACE_Composite", "SPACE_Risk_Band", "score_diff"]
]
print(divergent.to_string(index=False))

# ================================================================
# STEP 10: EXPORT ALL RESULTS
# ================================================================
print("\n" + "=" * 70)
print("STEP 10: Exporting results")
print("=" * 70)

# Save scored datasets
for name, df in [("train", df_train), ("validate", df_val), ("test", df_test)]:
    df.to_csv(OUTPUT_DIR / f"{name}_scored.csv", index=False)
    print(f"Saved: {OUTPUT_DIR / f'{name}_scored.csv'}")

# Save comparison summary as JSON
comparison_summary = {
    "dataset_info": {
        "total_records": len(df_final),
        "train_size": len(df_train),
        "validate_size": len(df_val),
        "test_size": len(df_test),
        "source_1": "ai_developer_productivity.csv (1000 rows, 100 unique devs)",
        "source_2": "Extended_Employee_Performance_and_Productivity_Data.csv (100000 rows)",
    },
    "pace_results_test": {
        "mean_ehs": round(df_test["EHS"].mean(), 4),
        "mean_opi": round(df_test["OPI"].mean(), 4),
        "mean_pace": round(df_test["PACE_Score"].mean(), 4),
        "std_pace": round(df_test["PACE_Score"].std(), 4),
        "risk_distribution": dict(df_test["PACE_Risk_Band"].value_counts()),
    },
    "space_results_test": {
        "mean_satisfaction": round(df_test["S_Satisfaction"].mean(), 4),
        "mean_performance": round(df_test["P_Performance"].mean(), 4),
        "mean_activity": round(df_test["A_Activity"].mean(), 4),
        "mean_communication": round(df_test["C_Communication"].mean(), 4),
        "mean_efficiency": round(df_test["E_Efficiency"].mean(), 4),
        "mean_composite": round(df_test["SPACE_Composite"].mean(), 4),
        "std_composite": round(df_test["SPACE_Composite"].std(), 4),
        "risk_distribution": dict(df_test["SPACE_Risk_Band"].value_counts()),
    },
    "comparison_metrics": {
        "risk_band_agreement": round(agreement, 4),
        "score_correlation_pearson_r": round(corr, 4),
        "mean_absolute_score_diff": round(df_compare["score_diff"].mean(), 4),
        "pace_cv": round(pace_cv, 4),
        "space_cv": round(space_cv, 4),
    },
}

with open(OUTPUT_DIR / "comparison_summary.json", "w") as f:
    json.dump(comparison_summary, f, indent=2, default=str)
print(f"Saved: {OUTPUT_DIR / 'comparison_summary.json'}")

# Save PACE-compatible dataset (just PACE fields) for the pipeline
pace_only_cols = ["employee_id", "employee_name", "team"] + pace_features
df_pace_ready = df_final[pace_only_cols].copy()
df_pace_ready.to_csv(DATASET_DIR / "pace_ready_merged.csv", index=False)
print(f"Saved PACE-ready dataset: {DATASET_DIR / 'pace_ready_merged.csv'}")

print("\n" + "=" * 70)
print("ALL STEPS COMPLETE")
print("=" * 70)
