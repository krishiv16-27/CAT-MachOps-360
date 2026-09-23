"""
Core entity generators: sites, zones, operators, machines.
Each function returns a list of dicts with full referential integrity.
"""
import random
from datetime import date, timedelta
from .faker_setup import fake, uid, MACHINE_CATALOGUE, CERTIFICATION_TYPES, FAULT_CODES, ZONE_TYPES
from .profiles import Profile


def generate_sites(profile: Profile, rng: random.Random) -> list[dict]:
    sites = []
    site_names = [
        "Alpha Construction Site", "Beta Mining Project", "Gamma Excavation Zone",
        "Delta Road Works", "Epsilon Open Cut Mine", "Zeta Infrastructure Hub",
        "Eta Civil Works", "Theta Demolition Site", "Iota Quarry Operations",
        "Kappa Rail Corridor", "Lambda Industrial Park", "Mu Coastal Development",
        "Nu Urban Renewal", "Xi Freeway Extension", "Omicron River Crossing",
        "Pi Tunnel Project", "Rho Landfill Expansion", "Sigma Airport Runway",
        "Tau Stadium Build", "Upsilon Wind Farm",
    ]
    for i in range(profile.num_sites):
        sites.append({
            "site_id": uid(),
            "site_code": f"SITE-{chr(65 + i):s}",
            "name": site_names[i % len(site_names)],
            "location": f"{fake.city()}, {fake.state_abbr()}",
            "latitude": rng.uniform(-38, -15),
            "longitude": rng.uniform(115, 153),
            "is_active": True,
        })
    return sites


def generate_zones(profile: Profile, sites: list[dict], rng: random.Random) -> list[dict]:
    zones = []
    zone_names = ["Excavation Zone", "Loading Bay", "Haul Road", "Dump Zone", "Workshop", "Safe Area",
                  "Fuel Station", "Maintenance Bay", "Control Zone", "Entry Gate"]
    for site in sites:
        for j in range(profile.num_zones_per_site):
            ztype = ZONE_TYPES[j % len(ZONE_TYPES)]
            zones.append({
                "zone_id": uid(),
                "site_id": site["site_id"],
                "zone_code": f"{site['site_code']}-Z{j + 1:02d}",
                "name": f"{zone_names[j % len(zone_names)]}",
                "zone_type": ztype,
                "speed_limit_kmh": rng.choice([10.0, 15.0, 20.0, 25.0]),
                "is_restricted": ztype in ("EXCAVATION", "LOADING_BAY"),
                "is_active": True,
            })
    return zones


def generate_machine_models(profile: Profile) -> list[dict]:
    models = []
    catalogue = MACHINE_CATALOGUE[:profile.num_machine_models]
    for m in catalogue:
        models.append({
            "model_id": uid(),
            **m,
            "manufacturer": "Caterpillar",
            "nominal_rpm_min": 800,
            "nominal_rpm_max": 2200,
        })
    return models


def generate_machines(
    profile: Profile,
    models: list[dict],
    sites: list[dict],
    zones: list[dict],
    rng: random.Random,
) -> list[dict]:
    machines = []
    type_to_models = {}
    for m in models:
        type_to_models.setdefault(m["machine_type"], []).append(m)

    statuses = ["ACTIVE"] * 7 + ["INACTIVE"] * 2 + ["MAINTENANCE"] * 1
    for i in range(profile.num_machines):
        model = models[i % len(models)]
        site = rng.choice(sites)
        zone_candidates = [z for z in zones if z["site_id"] == site["site_id"]]
        zone = rng.choice(zone_candidates) if zone_candidates else None
        year = rng.randint(2015, 2023)
        age_years = 2026 - year
        engine_hours = rng.uniform(200, 200 + age_years * 1500)
        status = statuses[i % len(statuses)]
        machines.append({
            "machine_id": uid(),
            "machine_code": f"{model['machine_type'][:3]}{i + 1:03d}",
            "model_id": model["model_id"],
            "site_id": site["site_id"],
            "zone_id": zone["zone_id"] if zone else None,
            "year_manufactured": year,
            "engine_hours": round(engine_hours, 1),
            "status": status,
            "is_active": True,
            "last_engine_temp_c": rng.uniform(80, 96),
            "last_fuel_level_pct": rng.uniform(30, 90),
            "last_machine_load_pct": rng.uniform(30, 75) if status == "ACTIVE" else 0,
            "last_speed_kmh": rng.uniform(0, 8) if status == "ACTIVE" else 0,
            "last_health_score": rng.uniform(75, 97),
            "current_operator_id": None,  # set after operators generated
            "current_task_id": None,
            "authorization_status": "AUTHORIZED" if status == "ACTIVE" else "PENDING",
        })
    return machines


def generate_operators(
    profile: Profile,
    sites: list[dict],
    machines: list[dict],
    rng: random.Random,
) -> list[dict]:
    operators = []
    machine_types = list(CERTIFICATION_TYPES.keys())

    for i in range(profile.num_operators):
        exp_years = rng.randint(1, 20)
        skill_level = min(5, max(1, int(exp_years / 4) + rng.randint(0, 1)))
        machine_type = rng.choice(machine_types)
        certs = CERTIFICATION_TYPES[machine_type]
        cert = certs[min(skill_level - 1, len(certs) - 1)]

        # 5% have expired certs (realistic)
        expiry_days = rng.choice([-30, -10, 90, 180, 365, 500, 700, 730]) if rng.random() > 0.95 else rng.randint(60, 730)
        expiry = date.today() + timedelta(days=expiry_days)

        site = rng.choice(sites)
        shift_active = rng.random() > 0.35
        ops_for_site = [m for m in machines if m["site_id"] == site["site_id"] and m["status"] == "ACTIVE"]
        current_machine = rng.choice(ops_for_site) if ops_for_site and shift_active else None

        op = {
            "operator_id": uid(),
            "employee_code": f"OP{1000 + i + 1}",
            "name": fake.name(),
            "email": None,
            "site_id": site["site_id"],
            "experience_years": exp_years,
            "skill_level": skill_level,
            "certification": cert,
            "certification_expiry": expiry.isoformat(),
            "is_active": True,
            "shift_status": "ON_SHIFT" if shift_active else "OFF_SHIFT",
            "continuous_operating_minutes": rng.uniform(10, 100) if shift_active else 0,
            "current_machine_id": current_machine["machine_id"] if current_machine else None,
            "current_task_id": None,
            "authorization_status": "AUTHORIZED" if shift_active else "PENDING",
            "safety_score": rng.uniform(70, 99),
        }
        operators.append(op)

        # Link machine to operator
        if current_machine:
            current_machine["current_operator_id"] = op["operator_id"]

    return operators


def generate_machine_maintenance(
    machines: list[dict],
    rng: random.Random,
) -> list[dict]:
    records = []
    maintenance_types = ["OIL_CHANGE", "FILTER", "HYDRAULIC_SERVICE", "FULL_SERVICE", "INSPECTION"]
    for machine in machines:
        num_records = rng.randint(1, 4)
        for j in range(num_records):
            days_ago = rng.randint(10, 365 * 3)
            records.append({
                "maintenance_id": uid(),
                "machine_id": machine["machine_id"],
                "maintenance_type": rng.choice(maintenance_types),
                "performed_at": (date.today() - timedelta(days=days_ago)).isoformat() + "T08:00:00Z",
                "engine_hours_at_service": max(0, machine["engine_hours"] - rng.uniform(100, 500)),
                "performed_by": "CAT Maintenance Team",
                "notes": None,
                "next_service_hours": machine["engine_hours"] + rng.uniform(400, 600),
            })
    return records


def generate_machine_faults(
    machines: list[dict],
    rng: random.Random,
    fault_probability: float = 0.15,
) -> list[dict]:
    faults = []
    for machine in machines:
        if rng.random() < fault_probability:
            code, desc, sev = rng.choice(FAULT_CODES)
            faults.append({
                "fault_id": uid(),
                "machine_id": machine["machine_id"],
                "fault_code": code,
                "fault_description": desc,
                "severity": sev,
                "detected_at": (date.today() - timedelta(days=rng.randint(0, 7))).isoformat() + "T10:00:00Z",
                "resolved_at": None,
                "is_active": True,
            })
    return faults


def generate_training_modules() -> list[dict]:
    modules = [
        ("Proximity Safety Awareness",        "SAFETY",            "VIDEO",      45,  True),
        ("Seatbelt & Personal Safety",         "SAFETY",            "VIDEO",      20,  True),
        ("Fuel Efficient Operation",           "MACHINE_OPERATION", "VIDEO",      30,  False),
        ("Safe Operating Speeds",              "MACHINE_OPERATION", "SIMULATION", 40,  True),
        ("Emergency Procedures",               "EMERGENCY",         "VIDEO",      60,  True),
        ("Excavator Advanced Operation",       "MACHINE_OPERATION", "SIMULATION", 90,  False),
        ("CAT 390F Machine Familiarisation",   "MACHINE_OPERATION", "VIDEO",      45,  True),
        ("Environmental Awareness",            "ENVIRONMENT",       "VIDEO",      25,  True),
        ("Hazard Identification",              "SAFETY",            "QUIZ",       30,  True),
        ("Pre-Start Inspection Procedure",     "SAFETY",            "VIDEO",      20,  True),
        ("Confined Space Awareness",           "SAFETY",            "VIDEO",      40,  True),
        ("Working at Heights",                 "SAFETY",            "VIDEO",      35,  True),
        ("Bulldozer Advanced Operation",       "MACHINE_OPERATION", "SIMULATION", 80,  False),
        ("Loader Operation Basics",            "MACHINE_OPERATION", "VIDEO",      45,  True),
        ("Fatigue Management",                 "SAFETY",            "VIDEO",      30,  True),
    ]
    return [
        {
            "module_id": uid(),
            "title": t, "category": c, "module_type": mt,
            "duration_minutes": dur, "is_mandatory": mand,
            "description": None, "machine_type": None, "is_active": True,
        }
        for t, c, mt, dur, mand in modules
    ]


def generate_operator_training(
    operators: list[dict],
    modules: list[dict],
    rng: random.Random,
) -> list[dict]:
    records = []
    for op in operators:
        for mod in modules:
            completion_chance = 0.80 if mod["is_mandatory"] else 0.45
            if rng.random() < completion_chance:
                completed_days_ago = rng.randint(10, 300)
                records.append({
                    "record_id": uid(),
                    "operator_id": op["operator_id"],
                    "module_id": mod["module_id"],
                    "status": "COMPLETED",
                    "started_at": (date.today() - timedelta(days=completed_days_ago + 1)).isoformat() + "T09:00:00Z",
                    "completed_at": (date.today() - timedelta(days=completed_days_ago)).isoformat() + "T10:30:00Z",
                    "score": rng.uniform(65, 100),
                    "expiry_date": (date.today() + timedelta(days=rng.randint(180, 730))).isoformat(),
                    "assigned_by": None,
                })
    return records
