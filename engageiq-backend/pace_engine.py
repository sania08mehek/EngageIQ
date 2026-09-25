def compute_ehs(meeting_load, focus_gap, response_latency, after_hours_ratio):
    # Normalized weights based on Algorithm Details (Algorithm Details.html)
    W1, W2, W3, W4 = 0.30, 0.30, 0.20, 0.20
    
    # Assume inputs are already normalized [0,1], where 1 is bad (high load).
    # So 1 - (...) gives health index where 1 is healthy.
    ehs = 1 - (W1 * meeting_load + W2 * focus_gap + W3 * response_latency + W4 * after_hours_ratio)
    
    # Clip between 0 and 1
    return max(0, min(1, ehs))

def compute_opi(completion_rate, velocity, deadline_adherence, code_activity, rework_ratio):
    # Normalized weights based on Algorithm Details
    W1, W2, W3, W4, W5 = 0.25, 0.25, 0.20, 0.20, 0.10
    
    # Rework is negative, others are positive. 
    opi = (W1 * completion_rate + W2 * velocity + W3 * deadline_adherence + W4 * code_activity) - (W5 * rework_ratio)
    
    return max(0, min(1, opi))

def compute_pace(ehs, opi):
    pace = (0.4 * ehs) + (0.6 * opi)
    return round(pace, 2)

def classify_risk(pace_score, persistent_anomaly=False):
    if pace_score >= 0.7:
        band = "Healthy"
    elif pace_score >= 0.4:
        band = "Moderate"
    else:
        band = "At-Risk"
        
    if persistent_anomaly and band != "At-Risk":
        band = "Moderate" if band == "Healthy" else "At-Risk"
        
    return band
