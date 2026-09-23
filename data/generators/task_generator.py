"""
Task and safety event generators.
Task durations are correlated with weather, terrain, operator skill, and machine type.
"""
import random
from datetime import datetime, timezone, timedelta
from .faker_setup import uid, TASK_TYPES, MATERIAL_TYPES, WEATHER_CONDITIONS, TERRAIN_TYPES
from .profiles import Profile


# Base duration minutes per task type
TASK_BASE_DURATION = {
    "EXCAVATION": 75,
    "LOADING":    45,
    "TRENCHING":  90,
    "GRADING":    60,
    "HAULING":    40,
    "COMPACTION": 50,
    "BACKFILL":   55,
}

# Duration multipliers
WEATHER_FACTOR = {"CLEAR": 1.0, "CLOUDY": 1.0, "RAIN": 1.25, "HEAVY_RAIN": 1.50, "FOG": 1.20, "DUST": 1.10}
TERRAIN_FACTOR = {"FLAT": 1.0, "SLOPE": 1.20, "ROUGH": 1.30, "ROCKY": 1.40, "WET": 1.35, "COMPACTED": 0.90}
SKILL_FACTOR   = {1: 1.35, 2: 1.15, 3: 1.00, 4: 0.88, 5: 0.78}


def _pick_task_type(rng: random.Random) -> str:
    types, weights = zip(*TASK_TYPES)
    return rng.choices(types, weights=weights, k=1)[0]


def _estimate_duration(task_type, weather, terrain, skill, rng: random.Random) -> float:
    base = TASK_BASE_DURATION.get(task_type, 60)
    wf = WEATHER_FACTOR.get(weather, 1.0)
    tf = TERRAIN_FACTOR.get(terrain, 1.0)
    sf = SKILL_FACTOR.get(skill, 1.0)
    noise = rng.uniform(0.85, 1.15)
    return round(base * wf * tf * sf * noise, 1)


def generate_tasks(
    profile: Profile,
    operators: list[dict],
    machines: list[dict],
    zones: list[dict],
    rng: random.Random,
) -> list[dict]:
    tasks = []
    now = datetime.now(timezone.utc)

    for op in operators:
        op_machines = [m for m in machines if m["site_id"] == op["site_id"] and m["status"] == "ACTIVE"]
        if not op_machines:
            op_machines = machines[:1]

        op_zones = [z for z in zones if z["site_id"] == op["site_id"]]
        if not op_zones:
            op_zones = zones[:1]

        # Generate tasks spread over the last 8 hours
        cursor = now - timedelta(hours=rng.uniform(6, 8))

        for t_idx in range(profile.num_tasks_per_operator):
            task_type = _pick_task_type(rng)
            weather = rng.choices(
                WEATHER_CONDITIONS,
                weights=[0.50, 0.20, 0.15, 0.05, 0.05, 0.05],
                k=1,
            )[0]
            terrain = rng.choices(
                TERRAIN_TYPES,
                weights=[0.45, 0.20, 0.15, 0.10, 0.07, 0.03],
                k=1,
            )[0]
            machine = rng.choice(op_machines)
            zone = rng.choice(op_zones)
            skill = op["skill_level"]
            est_dur = _estimate_duration(task_type, weather, terrain, skill, rng)
            actual_dur = est_dur * rng.uniform(0.80, 1.30)
            qty = rng.uniform(80, 800)

            actual_start = cursor
            actual_end = cursor + timedelta(minutes=actual_dur)

            # Determine status: past tasks completed, last one possibly in progress
            if actual_end < now - timedelta(minutes=10):
                status = "COMPLETED"
                completed_qty = qty
            elif actual_start < now:
                status = "IN_PROGRESS"
                progress = (now - actual_start).total_seconds() / (actual_dur * 60)
                completed_qty = qty * min(progress, 0.99)
                actual_end = None
                actual_dur = None
            else:
                status = "PENDING"
                completed_qty = 0
                actual_start = None
                actual_end = None
                actual_dur = None

            tasks.append({
                "task_id": uid(),
                "site_id": op["site_id"],
                "zone_id": zone["zone_id"],
                "machine_id": machine["machine_id"],
                "operator_id": op["operator_id"],
                "task_type": task_type,
                "description": f"{task_type.replace('_', ' ').title()} in {zone['name']}",
                "material_type": rng.choice(MATERIAL_TYPES),
                "target_quantity": round(qty, 1),
                "completed_quantity": round(completed_qty, 1),
                "unit": "m3",
                "status": status,
                "scheduled_start": actual_start.isoformat() if actual_start else None,
                "actual_start": actual_start.isoformat() if actual_start else None,
                "actual_end": actual_end.isoformat() if actual_end else None,
                "estimated_duration_minutes": est_dur,
                "actual_duration_minutes": round(actual_dur, 1) if actual_dur else None,
                "predicted_duration_minutes": round(est_dur * rng.uniform(0.95, 1.05), 1),
                "weather_condition": weather,
                "terrain_type": terrain,
                "delay_reason": rng.choice(["EQUIPMENT_ISSUE", "WEATHER", None, None, None]),
                "priority": rng.choice([1, 2, 2, 2, 3]),
            })

            # Advance cursor with a small break between tasks
            if actual_end:
                cursor = actual_end + timedelta(minutes=rng.uniform(5, 20))
            else:
                cursor = now + timedelta(minutes=rng.uniform(10, 60))

    return tasks


def generate_alerts_from_telemetry(
    telemetry: list[dict],
    machines_map: dict,
    rng: random.Random,
    alert_rate: float = 0.008,
) -> list[dict]:
    """Generate realistic alerts from telemetry data."""
    alerts = []
    now = datetime.now(timezone.utc)

    for row in telemetry:
        if rng.random() > alert_rate:
            continue

        # Choose alert type based on telemetry values
        alert_type = rng.choice([
            "PROXIMITY_WARNING", "SEATBELT_UNFASTENED",
            "EXCESSIVE_IDLING", "ENGINE_TEMP_WARNING",
        ])

        severity_map = {
            "PROXIMITY_WARNING": "MEDIUM",
            "SEATBELT_UNFASTENED": "HIGH",
            "EXCESSIVE_IDLING": "LOW",
            "ENGINE_TEMP_WARNING": "MEDIUM",
        }

        message_map = {
            "PROXIMITY_WARNING": "Person detected at 8.2m — proximity warning threshold.",
            "SEATBELT_UNFASTENED": "Seatbelt unfastened while machine in motion.",
            "EXCESSIVE_IDLING": f"Machine idle for {rng.randint(16, 30)} minutes.",
            "ENGINE_TEMP_WARNING": f"Engine temperature {rng.randint(106, 112)}°C — approaching critical threshold.",
        }

        alerts.append({
            "alert_id": uid(),
            "timestamp": row["timestamp"],
            "site_id": row.get("site_id"),
            "zone_id": row.get("zone_id"),
            "machine_id": row["machine_id"],
            "operator_id": row.get("operator_id"),
            "task_id": row.get("task_id"),
            "alert_type": alert_type,
            "severity": severity_map[alert_type],
            "trigger_data": {"source": "telemetry", "row_id": row["telemetry_id"]},
            "message": message_map[alert_type],
            "recommended_action": "Review and take appropriate action.",
            "acknowledged": rng.random() > 0.4,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "acknowledgement_note": None,
            "resolved": rng.random() > 0.7,
            "resolved_at": None,
        })

    return alerts


def generate_incidents(
    alerts: list[dict],
    rng: random.Random,
) -> list[dict]:
    """Auto-create incidents for CRITICAL/HIGH alerts."""
    incidents = []
    high_alerts = [a for a in alerts if a["severity"] in ("HIGH", "CRITICAL")]

    for alert in high_alerts:
        if rng.random() > 0.25:
            continue
        incidents.append({
            "incident_id": uid(),
            "timestamp": alert["timestamp"],
            "site_id": alert.get("site_id"),
            "zone_id": alert.get("zone_id"),
            "machine_id": alert.get("machine_id"),
            "operator_id": alert.get("operator_id"),
            "task_id": alert.get("task_id"),
            "alert_id": alert["alert_id"],
            "category": alert["alert_type"].split("_")[0],
            "severity": "HIGH" if alert["severity"] == "CRITICAL" else "MEDIUM",
            "description": f"Incident triggered by alert: {alert['message']}",
            "trigger_data": alert["trigger_data"],
            "evidence": [],
            "status": rng.choice(["OPEN", "INVESTIGATING", "RESOLVED"]),
            "assigned_to": None,
            "resolution": None,
            "root_cause": None,
            "corrective_action": None,
            "resolved_at": None,
            "is_auto_created": True,
        })

    return incidents


def generate_proximity_events(
    telemetry: list[dict],
    rng: random.Random,
    rate: float = 0.005,
) -> list[dict]:
    events = []
    for row in telemetry:
        if rng.random() > rate:
            continue
        dist = rng.uniform(2, 15)
        events.append({
            "event_id": uid(),
            "timestamp": row["timestamp"],
            "machine_id": row["machine_id"],
            "operator_id": row.get("operator_id"),
            "zone_id": row.get("zone_id"),
            "person_distance_m": round(dist, 1),
            "nearest_machine_distance_m": round(rng.uniform(5, 50), 1),
            "nearby_person_count": rng.randint(1, 3),
            "nearby_machine_count": rng.randint(0, 2),
            "restricted_zone_entry": dist < 5,
            "alert_id": None,
        })
    return events


def generate_dashcam_events(
    machines: list[dict],
    num_events: int,
    rng: random.Random,
) -> list[dict]:
    events = []
    now = datetime.now(timezone.utc)
    event_types = ["person_detected", "vehicle_detected", "obstacle_detected", "restricted_zone_entry"]

    for i in range(num_events):
        machine = rng.choice(machines)
        event_type = rng.choices(event_types, weights=[0.40, 0.30, 0.20, 0.10])[0]
        dist = rng.uniform(2, 25)
        ts = now - timedelta(minutes=rng.randint(1, 480))

        events.append({
            "event_id": uid(),
            "timestamp": ts.isoformat(),
            "camera_id": f"CAM-{machine['machine_code']}-FRONT",
            "machine_id": machine["machine_id"],
            "operator_id": machine.get("current_operator_id"),
            "person_detected": event_type in ("person_detected", "restricted_zone_entry"),
            "vehicle_detected": event_type == "vehicle_detected",
            "obstacle_detected": event_type == "obstacle_detected",
            "restricted_zone_entry": event_type == "restricted_zone_entry",
            "estimated_distance_m": round(dist, 1),
            "attention_event": rng.random() < 0.05,
            "eye_closure_event": rng.random() < 0.02,  # demo simulation only
            "yawn_event": rng.random() < 0.03,          # demo simulation only
            "confidence": round(rng.uniform(0.72, 0.97), 2),
            "event_type": event_type,
            "frame_path": None,
            "raw_metadata": {"source": "simulated"},
            "alert_id": None,
        })

    return events
