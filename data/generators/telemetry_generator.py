"""
Time-series telemetry generator.
Produces realistic correlated telemetry — values are NOT independent random numbers.
"""
import random
from datetime import datetime, timezone, timedelta
from .faker_setup import uid


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def generate_telemetry(
    machine: dict,
    operator: dict | None,
    task: dict | None,
    num_rows: int,
    rng: random.Random,
    start_time: datetime | None = None,
) -> list[dict]:
    """
    Generate a correlated time-series for one machine session.
    Values have realistic drift and correlation:
    - Engine temp rises with load
    - Fuel level decreases over time (faster at higher load)
    - Hydraulic pressure varies with activity
    - Idle time accumulates during pauses
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=num_rows)

    rows = []

    # Starting state
    engine_temp = rng.uniform(78, 88)
    fuel_level = rng.uniform(50, 95)
    oil_pressure = rng.uniform(45, 60)
    battery_v = rng.uniform(13.2, 14.4)
    hydraulic_pressure = rng.uniform(235, 260)
    operating_hours = machine.get("engine_hours", 1000)
    fuel_used_cumulative = 0.0
    cycle_count = 0
    idle_accum = 0.0

    # Machine load profile — varies over session
    base_load = rng.uniform(40, 70)

    for i in range(num_rows):
        ts = start_time + timedelta(minutes=i)

        # Load fluctuates realistically
        load_delta = rng.uniform(-8, 8)
        base_load = _clamp(base_load + load_delta, 10, 95)

        # Is machine working or idling?
        is_idle = rng.random() < 0.12  # ~12% idle time
        effective_load = 0 if is_idle else base_load

        # Engine temperature: rises with load, cools slowly
        target_temp = 82 + effective_load * 0.35
        engine_temp += (target_temp - engine_temp) * 0.05 + rng.uniform(-0.3, 0.3)
        engine_temp = _clamp(engine_temp, 70, 125)

        # Fuel: decreases with time and load
        consumption_rate = 8 + effective_load * 0.12  # L/hr
        consumption_this_min = consumption_rate / 60
        fuel_level = _clamp(fuel_level - consumption_this_min, 0, 100)
        fuel_used_cumulative += consumption_this_min

        # RPM: correlates with load
        if is_idle:
            rpm = rng.uniform(750, 900)
        else:
            rpm = 1000 + effective_load * 12 + rng.uniform(-80, 80)
            rpm = _clamp(rpm, 800, 2200)

        # Hydraulic pressure: varies with movement
        if is_idle:
            hydraulic_pressure = _clamp(hydraulic_pressure + rng.uniform(-5, 5), 180, 290)
        else:
            hydraulic_pressure = _clamp(hydraulic_pressure + rng.uniform(-15, 15), 190, 290)

        # Oil pressure: decreases slightly with engine hours
        oil_pressure = _clamp(oil_pressure + rng.uniform(-0.5, 0.5), 30, 75)

        # Battery voltage: mostly stable
        battery_v = _clamp(battery_v + rng.uniform(-0.05, 0.05), 11.8, 15.0)

        # Speed: 0 when idle, otherwise up to ~10 km/h for excavators
        speed = 0 if is_idle else rng.uniform(0, 10)

        # Cycle tracking
        if not is_idle and i % rng.randint(6, 12) == 0:
            cycle_count += 1

        # Idle accumulation
        idle_this_min = 1.0 if is_idle else 0.0
        idle_accum = min(idle_accum + idle_this_min, 60)  # reset capped at 60
        if not is_idle:
            idle_accum = max(0, idle_accum - 0.1)

        # Sudden events (5% chance)
        sudden_acc = rng.random() < 0.03
        sudden_brk = rng.random() < 0.02
        sudden_mov = rng.random() < 0.01

        # Seatbelt (97% compliance)
        seatbelt = "FASTENED" if rng.random() > 0.03 else "UNFASTENED"

        # Fault code injection (rare, ~1%)
        fault_code = None
        if rng.random() < 0.01:
            fault_code = rng.choice(["E-ENG-002", "E-HYD-042", "E-ELC-021"])

        operating_hours += 1 / 60

        rows.append({
            "telemetry_id": uid(),
            "timestamp": ts.isoformat(),
            "site_id": machine.get("site_id"),
            "zone_id": machine.get("zone_id"),
            "machine_id": machine["machine_id"],
            "operator_id": operator["operator_id"] if operator else None,
            "task_id": task["task_id"] if task else None,
            "engine_status": "IDLE" if is_idle else "RUNNING",
            "engine_rpm": round(rpm, 0),
            "engine_temperature_c": round(engine_temp, 1),
            "oil_pressure_psi": round(oil_pressure, 1),
            "coolant_temperature_c": round(engine_temp - rng.uniform(1, 5), 1),
            "battery_voltage": round(battery_v, 2),
            "fuel_level_pct": round(fuel_level, 1),
            "fuel_consumption_rate_lph": round(consumption_rate, 2),
            "fuel_used_l": round(fuel_used_cumulative, 2),
            "hydraulic_pressure_bar": round(hydraulic_pressure, 1),
            "hydraulic_temperature_c": round(45 + effective_load * 0.15 + rng.uniform(-2, 2), 1),
            "hydraulic_flow_lpm": round(100 + effective_load * 1.2 + rng.uniform(-10, 10), 1),
            "machine_speed_kmh": round(speed, 1),
            "machine_load_pct": round(effective_load, 1),
            "cycle_count": cycle_count,
            "cycle_time_min": round(rng.uniform(4, 9), 1) if not is_idle else 0,
            "idle_time_min": round(idle_accum, 1),
            "operating_hours": round(operating_hours, 3),
            "vibration_g": round(rng.uniform(0.1, 0.6) + effective_load * 0.004, 3),
            "fault_code": fault_code,
            "maintenance_status": "OK" if fault_code is None else "FAULT",
            "seatbelt_status": seatbelt,
            "sudden_acceleration": sudden_acc,
            "sudden_braking": sudden_brk,
            "sudden_movement": sudden_mov,
        })

    return rows


def generate_wearable_events(
    operator: dict,
    num_rows: int,
    rng: random.Random,
    start_time: datetime | None = None,
) -> list[dict]:
    """
    Generate wearable biometric events.
    Values are operational risk indicators ONLY — not medical diagnoses.
    """
    if start_time is None:
        start_time = datetime.now(timezone.utc) - timedelta(minutes=num_rows)

    rows = []
    heart_rate = rng.uniform(68, 85)
    fatigue = rng.uniform(0.05, 0.20)
    attention = rng.uniform(0.05, 0.15)
    battery = rng.uniform(70, 100)

    for i in range(num_rows):
        ts = start_time + timedelta(minutes=i)
        heart_rate_delta = rng.uniform(-3, 3)
        heart_rate = _clamp(heart_rate + heart_rate_delta, 55, 160)

        # Fatigue drifts up over a long shift
        fatigue_drift = 0.001 * (i / max(num_rows, 1))
        fatigue = _clamp(fatigue + rng.uniform(-0.01, 0.01) + fatigue_drift, 0, 1)
        attention = _clamp(attention + rng.uniform(-0.01, 0.01), 0, 1)
        battery = _clamp(battery - 0.02 + rng.uniform(-0.01, 0.01), 0, 100)

        rows.append({
            "event_id": uid(),
            "timestamp": ts.isoformat(),
            "operator_id": operator["operator_id"],
            "machine_id": operator.get("current_machine_id"),
            "heart_rate": round(heart_rate, 0),
            "heart_rate_delta": round(heart_rate_delta, 1),
            "activity_level": round(_clamp(rng.uniform(3, 8), 0, 10), 1),
            "motion_level": round(_clamp(rng.uniform(2, 7), 0, 10), 1),
            "skin_temperature_c": round(rng.uniform(35.2, 37.2), 1),
            "wearable_battery_pct": round(battery, 0),
            "wearable_connected": True,
            # Risk indicators — NOT medical diagnoses
            "attention_risk_indicator": round(attention, 3),
            "fatigue_risk_indicator": round(fatigue, 3),
            "self_reported_status": "FIT_FOR_WORK",
            "breathalyzer_status": None,  # Only present if explicitly simulated sensor
        })

    return rows


def generate_environmental_data(
    sites: list[dict],
    num_hours: int,
    rng: random.Random,
) -> list[dict]:
    rows = []
    base_time = datetime.now(timezone.utc) - timedelta(hours=num_hours)
    weather_states = ["CLEAR", "CLEAR", "CLOUDY", "CLOUDY", "RAIN", "FOG"]

    for site in sites:
        weather = rng.choice(weather_states)
        temp = rng.uniform(16, 34)

        for h in range(num_hours):
            ts = base_time + timedelta(hours=h)
            # Weather has persistence — changes ~10% per hour
            if rng.random() < 0.10:
                weather = rng.choice(weather_states)
            temp += rng.uniform(-1, 1)
            temp = _clamp(temp, 10, 42)
            rainfall = rng.uniform(0, 5) if weather in ("RAIN", "HEAVY_RAIN") else 0

            rows.append({
                "env_id": uid(),
                "timestamp": ts.isoformat(),
                "site_id": site["site_id"],
                "temperature_c": round(temp, 1),
                "humidity_pct": round(rng.uniform(30, 85), 1),
                "rainfall_mm": round(rainfall, 1),
                "wind_speed_kmh": round(rng.uniform(0, 35), 1),
                "visibility_m": round(rng.uniform(2000, 10000) if weather != "FOG" else rng.uniform(200, 1500), 0),
                "weather_condition": weather,
                "ground_condition": "WET" if rainfall > 1 else "DRY",
                "terrain_type": "FLAT",
                "dust_level": "HIGH" if weather == "CLEAR" and rng.random() > 0.6 else "LOW",
            })
    return rows
