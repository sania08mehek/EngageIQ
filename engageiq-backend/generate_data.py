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
    
    for i in range(50):
        emp_id = str(uuid.uuid4())[:8]
        emp_name = fake.name()
        team = random.choice(teams)
        
        # Determine target risk band: 30% Healthy, 50% Moderate, 20% At-Risk
        rand_cat = random.random()
        if rand_cat < 0.3:
            # Healthy: needs low EHS penalties (close to 0), high OPI rewards (close to 1)
            meeting_load = random.uniform(0, 0.3)
            focus_gap = random.uniform(0, 0.3)
            response_latency = random.uniform(0, 0.3)
            after_hours_ratio = random.uniform(0, 0.2)
            
            completion_rate = random.uniform(0.7, 1.0)
            velocity = random.uniform(0.6, 1.0)
            deadline_adherence = random.uniform(0.7, 1.0)
            code_activity = random.uniform(0.5, 1.0)
            rework_ratio = random.uniform(0, 0.2)
        elif rand_cat < 0.8:
            # Moderate
            meeting_load = random.uniform(0.3, 0.6)
            focus_gap = random.uniform(0.2, 0.5)
            response_latency = random.uniform(0.3, 0.6)
            after_hours_ratio = random.uniform(0.2, 0.5)
            
            completion_rate = random.uniform(0.4, 0.7)
            velocity = random.uniform(0.4, 0.7)
            deadline_adherence = random.uniform(0.4, 0.8)
            code_activity = random.uniform(0.3, 0.7)
            rework_ratio = random.uniform(0.1, 0.4)
        else:
            # At-Risk
            meeting_load = random.uniform(0.6, 1.0)
            focus_gap = random.uniform(0.5, 1.0)
            response_latency = random.uniform(0.6, 1.0)
            after_hours_ratio = random.uniform(0.5, 1.0)
            
            completion_rate = random.uniform(0.1, 0.4)
            velocity = random.uniform(0.1, 0.4)
            deadline_adherence = random.uniform(0.1, 0.4)
            code_activity = random.uniform(0.1, 0.4)
            rework_ratio = random.uniform(0.4, 1.0)
            
        writer.writerow([
            emp_id, emp_name, team["id"], team["name"],
            round(meeting_load, 2), round(focus_gap, 2), round(response_latency, 2), round(after_hours_ratio, 2),
            round(completion_rate, 2), round(velocity, 2), round(deadline_adherence, 2), round(code_activity, 2), round(rework_ratio, 2)
        ])

print("Generated sample_data.csv with 50 records.")
