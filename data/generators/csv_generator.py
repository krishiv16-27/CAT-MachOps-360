"""
CAT MachOps 360 — Story-Driven CSV Dataset Generator
=====================================================
Produces 9 rich CSV files in data/generated/ with deliberately planted
narrative patterns that tell a story judges can read at a glance.

Story anchors (seeded at demo, seed=42):
  - OP1009 has expired certification → pre-start fails
  - EXC004 (machine index 3) in maintenance 3 days → fault history visible
  - OP1001 (James Mitchell, index 0) has 4 self-corrected near-misses
  - One machine shows gradual hydraulic temperature rise over 2h
  - One operator's cycle times are 22% above personal baseline
  - Weather changes CLEAR→RAIN at hour 4 → visible task duration increase
  - OP1003 saves 18% more fuel than site average
"""
import csv
import math
import random
from datetime import datetime, date, timezone, timedelta
from pathlib import Path

# ── helpers ───────────────────────────────────────────────────────────────────

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

def _round(v, d=2):
    return round(v, d)

NOW = datetime.now(timezone.utc)


# ── 1. operators_profile.csv ─────────────────────────────────────────────────

OPERATOR_NAMES = [
    "James Mitchell",      # OP1001 — hero operator, 4 self-corrected near-misses
    "Sarah Chen",          # OP1002 — supervisor favourite
    "Marcus Williams",     # OP1003 — carbon savings leader (18% above avg)
    "Emily Rodriguez",     # OP1004
    "David Nguyen",        # OP1005
    "Priya Sharma",        # OP1006
    "Tom Anderson",        # OP1007
    "Lisa Thompson",       # OP1008
    "Alex Kowalski",       # OP1009 — EXPIRED CERTIFICATION
    "Ben Harrison",        # OP1010
]

SKILLS = [5, 4, 4, 3, 3, 3, 4, 2, 2, 3]
EXP    = [12, 8, 9, 5, 6, 4, 10, 3, 2, 7]
CERTS  = [
    "CAT-EXC-L4", "CAT-EXC-L3", "CAT-EXC-L3", "CAT-EXC-L2",
    "CAT-EXC-L2", "CAT-BUL-L2", "CAT-EXC-L4", "CAT-LDR-L1",
    "CAT-EXC-L1",  # OP1009 — expired
    "CAT-EXC-L2",
]


def generate_operators_profile(rng: random.Random) -> list[dict]:
    rows = []
    for i, name in enumerate(OPERATOR_NAMES):
        cert_code = CERTS[i]
        expired = (i == 8)  # OP1009
        expiry = (date.today() - timedelta(days=45)).isoformat() if expired else (date.today() + timedelta(days=rng.randint(60, 730))).isoformat()

        safety_base = 92 if i == 0 else rng.uniform(73, 98)  # James is top
        near_miss_self = 4 if i == 0 else rng.randint(0, 2)

        # OP1003 fuel efficiency
        fuel_eff = 0.94 if i == 2 else rng.uniform(0.78, 1.02)

        tasks_today = rng.randint(2, 6)
        idle_today = rng.uniform(3, 25)

        anomaly = "NORMAL"
        if i == 8:
            anomaly = "UNUSUAL"  # expired cert operator flagged
        elif i == 4:
            anomaly = "UNUSUAL"  # cycle-time anomaly operator

        training_pct = 95 if i == 0 else (100 if i == 1 else rng.uniform(60, 100))

        # carbon saved
        baseline_fuel = 42 + rng.uniform(-3, 3)
        fuel_eff_ratio = fuel_eff
        actual_fuel = baseline_fuel * fuel_eff_ratio
        saved = baseline_fuel - actual_fuel
        carbon = _round(max(0, saved) * 2.68, 2)

        rows.append({
            "name": name,
            "employee_code": f"OP10{i+1:02d}",
            "experience_years": EXP[i],
            "skill_level": SKILLS[i],
            "certification": cert_code,
            "certification_expiry": expiry,
            "certification_valid": "NO" if expired else "YES",
            "safety_score": _round(safety_base, 1),
            "tasks_completed_today": tasks_today,
            "idle_time_today_min": _round(idle_today, 1),
            "fuel_efficiency_score": _round(fuel_eff, 3),
            "anomaly_label": anomaly,
            "training_completion_pct": _round(training_pct, 1),
            "carbon_saved_kg": carbon,
            "near_miss_self_corrected_count": near_miss_self,
        })
    return rows


# ── 2. machine_health_snapshot.csv ───────────────────────────────────────────

MACHINE_CODES = [
    "EXC001", "EXC002", "EXC003", "EXC004",   # EXC004 in maintenance
    "BUL001", "BUL002",
    "LDR001", "LDR002",
    "GRD001",
    "TRK001",
]
MACHINE_TYPES = [
    "EXCAVATOR","EXCAVATOR","EXCAVATOR","EXCAVATOR",
    "BULLDOZER","BULLDOZER",
    "LOADER","LOADER",
    "GRADER",
    "DUMP_TRUCK",
]


def generate_machine_health(rng: random.Random) -> list[dict]:
    rows = []
    for i, (code, mtype) in enumerate(zip(MACHINE_CODES, MACHINE_TYPES)):
        in_maint = (i == 3)  # EXC004
        if in_maint:
            engine_h = 18
            fuel_h = 100
            hydr_h = 62
            mech_h = 55
            overall = 72
            temp = 78
            fuel_pct = 45
            hours_since = 72  # 3 days
            maint_risk = "HIGH"
        else:
            engine_h = rng.uniform(88, 99)
            fuel_h = rng.uniform(82, 99)
            hydr_h = rng.uniform(80, 99)
            mech_h = rng.uniform(78, 99)
            overall = (engine_h * 0.30 + fuel_h * 0.15 + hydr_h * 0.20 + mech_h * 0.15 + rng.uniform(85, 99) * 0.10 + rng.uniform(85, 99) * 0.10)
            temp = rng.uniform(80, 95)
            fuel_pct = rng.uniform(35, 90)
            hours_since = rng.uniform(12, 400)
            maint_risk = "LOW" if overall > 88 else "MEDIUM"

        rows.append({
            "machine_code": code,
            "machine_type": mtype,
            "status": "MAINTENANCE" if in_maint else "ACTIVE",
            "engine_health_score": _round(engine_h, 1),
            "fuel_health_score": _round(fuel_h, 1),
            "hydraulic_health_score": _round(hydr_h, 1),
            "mechanical_health_score": _round(mech_h, 1),
            "overall_health": _round(overall, 1),
            "engine_temp_c": _round(temp, 1),
            "fuel_level_pct": _round(fuel_pct, 1),
            "hours_since_service": _round(hours_since, 1),
            "predicted_maintenance_risk": maint_risk,
            "notes": "In maintenance for 3 days — fault history logged" if in_maint else "",
        })
    return rows


# ── 3. telemetry_correlated.csv ───────────────────────────────────────────────
# 120 rows per ACTIVE machine (EXC004 excluded)
# Special patterns:
#   EXC001 — gradual hydraulic temp rise over 2h (silent risk)
#   OP1005 (EXC003) — cycle times 22% above personal baseline
#   Weather switches CLEAR→RAIN at row 240 (machine index 0, hour 4)

def generate_telemetry_correlated(rng: random.Random) -> list[dict]:
    rows = []
    active_machines = [(c, t) for i, (c, t) in enumerate(zip(MACHINE_CODES, MACHINE_TYPES)) if i != 3]

    for m_idx, (code, mtype) in enumerate(active_machines):
        engine_temp = rng.uniform(81, 87)
        fuel_level = rng.uniform(55, 90)
        hydraulic_temp = 42.0
        rpm_base = 1400 + rng.uniform(-100, 100)
        load_base = rng.uniform(45, 65)
        cycle_baseline = rng.uniform(5.5, 7.5)
        weather = "CLEAR"

        for row_i in range(120):
            ts = (NOW - timedelta(minutes=120 - row_i)).isoformat()

            # Weather changes at row 60 (hour 1 boundary) for first machine
            if m_idx == 0 and row_i == 60:
                weather = "RAIN"

            is_idle = rng.random() < 0.10
            load_delta = rng.uniform(-6, 6)
            load_base = _clamp(load_base + load_delta, 10, 90)
            effective_load = 0 if is_idle else load_base

            # Engine temp
            target = 83 + effective_load * 0.3 + (3 if weather == "RAIN" else 0)
            engine_temp += (target - engine_temp) * 0.05 + rng.uniform(-0.2, 0.2)
            engine_temp = _clamp(engine_temp, 75, 118)

            # SPECIAL: EXC001 hydraulic temp gradually rises over 2h
            if m_idx == 0:
                hydraulic_temp = 42 + (row_i / 120) * 28 + rng.uniform(-1, 1)  # 42→70°C
            else:
                hydraulic_temp = 44 + effective_load * 0.15 + rng.uniform(-2, 2)
            hydraulic_temp = _clamp(hydraulic_temp, 35, 85)

            # Fuel
            consumption = (8 + effective_load * 0.12) * (1.15 if weather == "RAIN" else 1.0)
            fuel_level = _clamp(fuel_level - consumption / 60, 0, 100)

            # RPM
            rpm = 0 if is_idle else _clamp(rpm_base + effective_load * 8 + rng.uniform(-60, 60), 800, 2200)

            # Hydraulic pressure
            hydr_pres = _clamp(245 + rng.uniform(-20, 20) if not is_idle else 210 + rng.uniform(-10, 10), 180, 290)

            # Speed
            speed = 0 if is_idle else rng.uniform(0, 10 if mtype == "EXCAVATOR" else 25)

            # Cycle time — OP1005 machine (m_idx 2 = EXC003) 22% above baseline
            if m_idx == 2:
                cycle_t = cycle_baseline * 1.22 + rng.uniform(-0.3, 0.3) if not is_idle else 0
            else:
                cycle_t = cycle_baseline + rng.uniform(-0.5, 0.5) if not is_idle else 0

            idle_min = rng.uniform(0.8, 1.5) if is_idle else 0

            rows.append({
                "timestamp": ts,
                "machine_code": code,
                "machine_type": mtype,
                "weather_condition": weather,
                "rpm": round(rpm, 0),
                "engine_temp_c": _round(engine_temp, 1),
                "fuel_level_pct": _round(fuel_level, 1),
                "load_pct": _round(effective_load, 1),
                "hydraulic_pressure_bar": _round(hydr_pres, 1),
                "hydraulic_temp_c": _round(hydraulic_temp, 1),
                "speed_kmh": _round(speed, 1),
                "idle_time_min": _round(idle_min, 2),
                "seatbelt_status": "FASTENED" if rng.random() > 0.03 else "UNFASTENED",
                "sudden_acceleration": rng.random() < 0.03,
                "cycle_count": row_i // 8,
                "fuel_consumption_rate_lph": _round(consumption, 2),
                "anomaly_flag": "YES" if (m_idx == 0 and hydraulic_temp > 62) else "NO",
            })
    return rows


# ── 4. safety_events_enriched.csv ────────────────────────────────────────────

ALERT_TYPES = [
    ("PROXIMITY_WARNING", "MEDIUM"),
    ("SEATBELT_UNFASTENED", "HIGH"),
    ("EXCESSIVE_IDLING", "LOW"),
    ("ENGINE_TEMP_WARNING", "MEDIUM"),
    ("SPEED_VIOLATION", "HIGH"),
    ("BREAK_RECOMMENDATION", "LOW"),
    ("PROXIMITY_CRITICAL", "CRITICAL"),
]


def generate_safety_events(rng: random.Random) -> list[dict]:
    rows = []
    for i, name in enumerate(OPERATOR_NAMES):
        num_events = rng.randint(1, 6)
        for j in range(num_events):
            atype, severity = rng.choice(ALERT_TYPES)
            mins_ago = rng.randint(5, 480)
            ts = (NOW - timedelta(minutes=mins_ago)).isoformat()
            machine = rng.choice(MACHINE_CODES[:9])  # not EXC004

            # James: always self-corrects
            self_corrected = True if i == 0 else rng.random() < 0.35
            resp_time = rng.uniform(1.5, 8) if self_corrected else rng.uniform(6, 25)

            # Trigger values based on type
            if atype == "PROXIMITY_WARNING":
                trigger = f"person_distance_m={_round(rng.uniform(6, 9.9), 1)}"
            elif atype == "SEATBELT_UNFASTENED":
                trigger = f"speed_kmh={_round(rng.uniform(1, 8), 1)}"
            elif atype == "EXCESSIVE_IDLING":
                trigger = f"idle_minutes={rng.randint(16, 35)}"
            elif atype in ("ENGINE_TEMP_WARNING", "PROXIMITY_CRITICAL"):
                trigger = f"value={_round(rng.uniform(106, 118), 1)}"
            else:
                trigger = f"speed_kmh={_round(rng.uniform(22, 30), 1)}"

            outcome = "SAFE_OUTCOME" if self_corrected else ("INCIDENT_LOGGED" if severity == "CRITICAL" else "ACKNOWLEDGED")

            rows.append({
                "timestamp": ts,
                "operator_name": name,
                "employee_code": f"OP10{i+1:02d}",
                "machine_code": machine,
                "alert_type": atype,
                "severity": severity,
                "trigger_values": trigger,
                "was_self_corrected": "YES" if self_corrected else "NO",
                "response_time_seconds": _round(resp_time, 1),
                "outcome": outcome,
            })
    return sorted(rows, key=lambda r: r["timestamp"])


# ── 5. task_performance.csv ───────────────────────────────────────────────────

def generate_task_performance(rng: random.Random) -> list[dict]:
    rows = []
    base_durations = {
        "EXCAVATION": 75, "LOADING": 45, "TRENCHING": 90,
        "GRADING": 60, "HAULING": 40, "COMPACTION": 50, "BACKFILL": 55,
    }
    weather_list = ["CLEAR", "CLEAR", "CLOUDY", "RAIN", "RAIN", "FOG"]
    terrain_list = ["FLAT", "FLAT", "SLOPE", "ROUGH", "ROCKY"]

    for i, name in enumerate(OPERATOR_NAMES):
        for t_idx in range(4):
            task_type = list(base_durations.keys())[rng.randint(0, 6)]
            weather = weather_list[rng.randint(0, 5)]
            terrain = terrain_list[rng.randint(0, 4)]
            skill = SKILLS[i]
            base = base_durations[task_type]
            wf = {"CLEAR": 1.0, "CLOUDY": 1.0, "RAIN": 1.28, "FOG": 1.20}.get(weather, 1.0)
            tf = {"FLAT": 1.0, "SLOPE": 1.20, "ROUGH": 1.30, "ROCKY": 1.40}.get(terrain, 1.0)
            sf = {5: 0.78, 4: 0.88, 3: 1.00, 2: 1.15, 1: 1.35}.get(skill, 1.0)
            est = base * wf * tf * sf
            actual = est * rng.uniform(0.82, 1.25)
            predicted = est * rng.uniform(0.90, 1.10)
            accuracy = 100 - abs((predicted - actual) / actual) * 100
            qty = rng.uniform(100, 600)
            fuel = actual * 0.18 + rng.uniform(-2, 5)
            carbon = fuel * 2.68

            rows.append({
                "task_type": task_type,
                "operator_name": name,
                "employee_code": f"OP10{i+1:02d}",
                "machine_code": rng.choice(MACHINE_CODES[:9]),
                "weather": weather,
                "terrain": terrain,
                "skill_level": skill,
                "estimated_duration_min": _round(est, 1),
                "actual_duration_min": _round(actual, 1),
                "eta_predicted_min": _round(predicted, 1),
                "eta_accuracy_pct": _round(accuracy, 1),
                "material_moved_m3": _round(qty, 1),
                "fuel_used_l": _round(fuel, 1),
                "carbon_kg": _round(carbon, 2),
            })
    return rows


# ── 6. operator_machine_pairing.csv ──────────────────────────────────────────

def _compatibility_reason(op_name, machine_code, score):
    if score >= 85:
        return f"{op_name.split()[0]} has proven performance on this machine type"
    elif score >= 70:
        return f"Good match — minor experience gap in terrain conditions"
    else:
        return f"Below optimal — recommend additional training before assignment"


def generate_operator_machine_pairing(rng: random.Random) -> list[dict]:
    rows = []
    for i, name in enumerate(OPERATOR_NAMES):
        machines_scored = rng.sample(MACHINE_CODES[:9], k=min(5, 9))
        for m_code in machines_scored:
            exp_match = min(100, EXP[i] * 7 + rng.uniform(-5, 5))
            familiarity = rng.uniform(40, 95)
            task_match = rng.uniform(55, 98)
            cond_match = rng.uniform(60, 98)
            machine_cond = 90 if "EXC004" not in m_code else 45
            score = (exp_match * 0.20 + familiarity * 0.25 + task_match * 0.20 + cond_match * 0.20 + machine_cond * 0.15)
            # Expired cert → low score
            if i == 8:
                score = score * 0.55
            score = _clamp(score, 10, 100)
            label = "EXCELLENT" if score >= 88 else ("SUITABLE" if score >= 70 else "NOT RECOMMENDED")
            recommended = "YES" if score >= 70 and i != 8 else "NO"

            rows.append({
                "operator_name": name,
                "employee_code": f"OP10{i+1:02d}",
                "machine_code": m_code,
                "compatibility_score_pct": _round(score, 1),
                "experience_match_pct": _round(exp_match, 1),
                "familiarity_score_pct": _round(familiarity, 1),
                "task_match_pct": _round(task_match, 1),
                "label": label,
                "recommended": recommended,
                "reason": _compatibility_reason(name, m_code, score),
            })
    return rows


# ── 7. near_miss_log.csv ──────────────────────────────────────────────────────

def generate_near_miss_log(rng: random.Random) -> list[dict]:
    rows = []

    # OP1001 (James) has 4 confirmed self-corrected near-misses
    for j in range(4):
        dist = rng.uniform(4.8, 7.5)
        resp = rng.uniform(1.2, 3.8)
        rows.append({
            "timestamp": (NOW - timedelta(hours=rng.randint(1, 48))).isoformat(),
            "operator_name": "James Mitchell",
            "employee_code": "OP1001",
            "machine_code": rng.choice(["EXC001", "EXC002"]),
            "person_distance_m": _round(dist, 1),
            "operator_response_time_sec": _round(resp, 1),
            "was_self_corrected_before_alert": "YES",
            "severity_if_not_caught": "HIGH" if dist < 5.5 else "MEDIUM",
            "machine_speed_reduction_pct": _round(rng.uniform(55, 100), 1),
        })

    # Other operators: occasional
    for i, name in enumerate(OPERATOR_NAMES[1:], 1):
        count = rng.randint(0, 2)
        for j in range(count):
            dist = rng.uniform(3.2, 9.8)
            resp = rng.uniform(1.5, 18)
            self_corrected = dist > 5.5 and rng.random() < 0.5
            rows.append({
                "timestamp": (NOW - timedelta(hours=rng.randint(1, 72))).isoformat(),
                "operator_name": name,
                "employee_code": f"OP10{i+1:02d}",
                "machine_code": rng.choice(MACHINE_CODES[:9]),
                "person_distance_m": _round(dist, 1),
                "operator_response_time_sec": _round(resp, 1),
                "was_self_corrected_before_alert": "YES" if self_corrected else "NO",
                "severity_if_not_caught": "CRITICAL" if dist < 4 else ("HIGH" if dist < 6 else "MEDIUM"),
                "machine_speed_reduction_pct": _round(rng.uniform(40, 100), 1) if self_corrected else 0,
            })

    return sorted(rows, key=lambda r: r["timestamp"])


# ── 8. carbon_passport.csv ────────────────────────────────────────────────────

def generate_carbon_passport(rng: random.Random) -> list[dict]:
    rows = []
    # Site average baseline fuel per shift (litres)
    site_avg_fuel = 44.0

    fuels = []
    for i, name in enumerate(OPERATOR_NAMES):
        # OP1003 saves 18% more than average
        if i == 2:
            fuel = site_avg_fuel * 0.82
        elif i == 8:  # expired cert — inefficient
            fuel = site_avg_fuel * 1.12
        else:
            fuel = site_avg_fuel * rng.uniform(0.88, 1.09)
        fuels.append(fuel)

    site_fuel_used = sum(fuels) / len(fuels)

    for i, name in enumerate(OPERATOR_NAMES):
        fuel = fuels[i]
        baseline = site_avg_fuel
        saved = baseline - fuel
        co2_saved = saved * 2.68
        trees = co2_saved / 21.7
        idle_min = rng.uniform(3, 22)
        idle_saved = max(0, 15 - idle_min)
        site_rank = 1 if i == 2 else (10 if i == 8 else rng.randint(2, 9))

        rows.append({
            "operator_name": name,
            "employee_code": f"OP10{i+1:02d}",
            "fuel_used_l": _round(fuel, 1),
            "baseline_fuel_l": _round(baseline, 1),
            "fuel_saved_l": _round(saved, 1),
            "idle_minutes": _round(idle_min, 1),
            "idle_saved_minutes": _round(idle_saved, 1),
            "co2_saved_kg": _round(co2_saved, 2),
            "trees_equivalent": _round(trees, 2),
            "site_rank": site_rank,
            "site_rank_percentile": _round((10 - site_rank) / 9 * 100, 0),
            "carbon_rating": "EXCELLENT" if co2_saved > 5 else ("GOOD" if co2_saved > 0 else "BELOW_AVERAGE"),
        })

    return rows


# ── writer ────────────────────────────────────────────────────────────────────

def write_csvs(out_dir: Path, seed: int = 42) -> dict[str, int]:
    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)

    datasets = {
        "operators_profile":         generate_operators_profile(rng),
        "machine_health_snapshot":   generate_machine_health(rng),
        "telemetry_correlated":      generate_telemetry_correlated(rng),
        "safety_events_enriched":    generate_safety_events(rng),
        "task_performance":          generate_task_performance(rng),
        "operator_machine_pairing":  generate_operator_machine_pairing(rng),
        "near_miss_log":             generate_near_miss_log(rng),
        "carbon_passport":           generate_carbon_passport(rng),
    }

    counts = {}
    for name, rows in datasets.items():
        if not rows:
            counts[name] = 0
            continue
        path = out_dir / f"{name}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        counts[name] = len(rows)
        print(f"  {name:35s}: {len(rows):>5} rows → {path.name}")

    return counts


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "generated"
    print("\nCAT MachOps 360 — CSV Generator")
    print("=" * 50)
    counts = write_csvs(out)
    total = sum(counts.values())
    print(f"\nTotal rows: {total:,}")
    print(f"Output dir: {out}")
