import csv
import random
import uuid
import faker

fake = faker.Faker()

teams = [
    {"id": "platform", "name": "Platform Engineering"},
    {"id": "design", "name": "Product Design"},
    {"id": "sales", "name": "Enterprise Sales"},
    {"id": "data-ml", "name": "Data and ML"},
    {"id": "marketing", "name": "Growth Marketing"},
    {"id": "support", "name": "Customer Support"},
    {"id": "core", "name": "Core Infrastructure"}
]

columns = [
    "employee_id", "employee_name", "team_id", "team_name",
    "meeting_load", "focus_gap", "response_latency", "after_hours_ratio",
    "completion_rate", "velocity", "deadline_adherence", "code_activity", "rework_ratio"
]

with open("sample_data.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    
    for i in range(52,):
        emp_id = str(uuid.uuid4())[:8]
        emp_name = fake.name()
        team = random.choice(teams)
        
        # random realistic distribution
        meeting_load = round(random.uniform(5, 30), 1)
        focus_gap = round(random.uniform(0, 10), 1)
        response_latency = round(random.uniform(0.5, 24), 1)
        after_hours_ratio = round(random.uniform(0, 40), 1)
        
        completion_rate = round(random.uniform(50, 100), 1)
        velocity = round(random.uniform(2, 20), 1)
        deadline_adherence = round(random.uniform(40, 100), 1)
        code_activity = round(random.uniform(0, 50), 1)
        rework_ratio = round(random.uniform(0, 30), 1)
        
        writer.writerow([
            emp_id, emp_name, team["id"], team["name"],
            meeting_load, focus_gap, response_latency, after_hours_ratio,
            completion_rate, velocity, deadline_adherence, code_activity, rework_ratio
        ])

print("Generated sample_data.csv with 50 records.")
