"""
EngageIQ Data Pipeline - Synthetic Dataset Generator
Generates realistic multi-role employee datasets with work signals and output metrics.
"""

import csv
import random
from pathlib import Path

ROLES = ["Engineer", "Designer", "Salesperson", "Manager"]

TEAMS = [
    ("platform", "Platform Engineering"),
    ("design", "Product Design"),
    ("sales", "Enterprise Sales"),
    ("data-ml", "Data & Machine Learning"),
    ("marketing", "Growth Marketing"),
    ("support", "Customer Support"),
    ("core", "Core Backend"),
]

FIRST_NAMES = [
    "Aria", "Liam", "Sophia", "Noah", "Olivia", "James", "Emma", "Lucas",
    "Ava", "Mason", "Isabella", "Ethan", "Mia", "Oliver", "Harper", "Elijah",
    "Evelyn", "Aiden", "Abigail", "Daniel", "Emily", "Matthew", "Ella", "Henry",
    "Madison", "Alexander", "Scarlett", "Sebastian", "Victoria", "David"
]

LAST_NAMES = [
    "Chen", "Smith", "Patel", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee"
]


def generate_employee_row(emp_id_num: int, target_profile: str = "healthy"):
    """
    Generates a realistic employee data row matching a specific risk profile.
    
    target_profile: 'healthy', 'moderate', 'at_risk', or 'collab_drop'
    """
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    name = f"{first} {last}"
    emp_id = f"EMP-{emp_id_num:04d}"
    
    role = random.choice(ROLES)
    team_id, team_name = random.choice(TEAMS)
    
    # Profile-driven signal and output values
    if target_profile == "healthy":
        # Low meeting overload, low after-hours, high outputs, low rework
        meeting_hours = round(random.uniform(4.0, 12.0), 1)
        focus_gap_days = round(random.uniform(0.0, 1.5), 1)
        response_latency_hours = round(random.uniform(0.5, 3.0), 1)
        after_hours_pct = round(random.uniform(2.0, 8.0), 1)
        
        task_completion_rate = round(random.uniform(0.80, 0.98), 2)
        velocity = round(random.uniform(0.82, 1.05), 2)
        deadline_adherence = round(random.uniform(0.85, 1.0), 2)
        code_activity = round(random.uniform(0.70, 0.95), 2)
        rework_ratio = round(random.uniform(0.02, 0.10), 2)

    elif target_profile == "moderate":
        # Moderate signals and outputs
        meeting_hours = round(random.uniform(14.0, 22.0), 1)
        focus_gap_days = round(random.uniform(1.8, 3.2), 1)
        response_latency_hours = round(random.uniform(3.5, 7.0), 1)
        after_hours_pct = round(random.uniform(10.0, 20.0), 1)
        
        task_completion_rate = round(random.uniform(0.60, 0.79), 2)
        velocity = round(random.uniform(0.60, 0.80), 2)
        deadline_adherence = round(random.uniform(0.65, 0.80), 2)
        code_activity = round(random.uniform(0.50, 0.70), 2)
        rework_ratio = round(random.uniform(0.12, 0.22), 2)

    elif target_profile == "collab_drop":
        # High meeting load & after-hours, but output still held up (classic burnout signal)
        meeting_hours = round(random.uniform(24.0, 32.0), 1)
        focus_gap_days = round(random.uniform(3.5, 5.0), 1)
        response_latency_hours = round(random.uniform(8.0, 14.0), 1)
        after_hours_pct = round(random.uniform(25.0, 38.0), 1)
        
        task_completion_rate = round(random.uniform(0.75, 0.88), 2)
        velocity = round(random.uniform(0.70, 0.85), 2)
        deadline_adherence = round(random.uniform(0.75, 0.90), 2)
        code_activity = round(random.uniform(0.65, 0.80), 2)
        rework_ratio = round(random.uniform(0.10, 0.18), 2)

    else:  # at_risk
        # High friction across all dimensions
        meeting_hours = round(random.uniform(22.0, 36.0), 1)
        focus_gap_days = round(random.uniform(3.0, 5.0), 1)
        response_latency_hours = round(random.uniform(7.0, 16.0), 1)
        after_hours_pct = round(random.uniform(22.0, 45.0), 1)
        
        task_completion_rate = round(random.uniform(0.30, 0.55), 2)
        velocity = round(random.uniform(0.30, 0.55), 2)
        deadline_adherence = round(random.uniform(0.35, 0.58), 2)
        code_activity = round(random.uniform(0.20, 0.45), 2)
        rework_ratio = round(random.uniform(0.25, 0.45), 2)

    # Derived normalized ratios [0, 1] for signal columns (where 1 = heavy load/bad)
    # Role-adjusted baseline maximums
    max_meetings = 32.0 if role == "Manager" else 24.0
    meeting_load = round(min(1.0, max(0.0, meeting_hours / max_meetings)), 2)
    focus_gap = round(min(1.0, max(0.0, focus_gap_days / 5.0)), 2)
    max_latency = 14.0 if role != "Salesperson" else 6.0
    response_latency = round(min(1.0, max(0.0, response_latency_hours / max_latency)), 2)
    after_hours_ratio = round(min(1.0, max(0.0, after_hours_pct / 40.0)), 2)

    return {
        "employee_id": emp_id,
        "employee_name": name,
        "role": role,
        "team_id": team_id,
        "team_name": team_name,
        # Human readable metrics
        "meeting_hours": meeting_hours,
        "focus_gap_days": focus_gap_days,
        "response_latency_hours": response_latency_hours,
        "after_hours_pct": after_hours_pct,
        # Normalized metrics (compatible with backend upload requirements)
        "meeting_load": meeting_load,
        "focus_gap": focus_gap,
        "response_latency": response_latency,
        "after_hours_ratio": after_hours_ratio,
        # Output metrics
        "completion_rate": task_completion_rate,
        "velocity": velocity,
        "deadline_adherence": deadline_adherence,
        "code_activity": code_activity,
        "rework_ratio": rework_ratio,
    }


def generate_csv(output_path: str, count: int = 40):
    """Generates the employee dataset CSV."""
    rows = []
    # Mix: 45% healthy, 35% moderate, 10% collab_drop, 10% at_risk
    profiles = (
        ["healthy"] * int(count * 0.45) +
        ["moderate"] * int(count * 0.35) +
        ["collab_drop"] * int(count * 0.10) +
        ["at_risk"] * int(count * 0.10)
    )
    random.shuffle(profiles)
    
    for i, profile in enumerate(profiles, start=1):
        rows.append(generate_employee_row(i, target_profile=profile))

    fieldnames = list(rows[0].keys())
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Dataset successfully created at {output_path} with {len(rows)} employees.")


if __name__ == "__main__":
    target = Path(__file__).resolve().parent / "employees_sample.csv"
    generate_csv(str(target), count=50)
