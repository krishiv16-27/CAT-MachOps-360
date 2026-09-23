"""
Demo data seeder.
Creates a minimal, realistic dataset for the demo profile.
Run automatically on startup if AUTO_SEED_ON_STARTUP=true and DB is empty.
"""
import uuid
import random
from datetime import datetime, timezone, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from .database import AsyncSessionLocal
from .security import hash_password
from ..models.user import User
from ..models.site import Site, Zone
from ..models.operator import Operator, OperatorCertification, OperatorBreak
from ..models.machine import Machine, MachineModel, MachineMaintenance
from ..models.task import Task, TaskEvent
from ..models.telemetry import Telemetry, WearableEvent, EnvironmentalData
from ..models.safety import Alert, Incident, PrestartCheck, MachinePermission, DashcamEvent
from ..models.training import TrainingModule, OperatorTraining, TrainingRecommendation
import logging

logger = logging.getLogger(__name__)
rng = random.Random(42)  # Deterministic seed


def uid(): return str(uuid.uuid4())


async def seed_demo_data():
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        count = (await db.execute(select(func.count()).select_from(User))).scalar()
        if count and count > 0:
            logger.info("Demo data already seeded. Skipping.")
            return

        logger.info("Seeding demo data...")

        # ── Sites ──────────────────────────────────────────────────────
        site1_id = uid()
        site2_id = uid()
        db.add(Site(site_id=site1_id, site_code="SITE-ALPHA", name="Alpha Construction Site", location="Brisbane, QLD", latitude=-27.47, longitude=153.02))
        db.add(Site(site_id=site2_id, site_code="SITE-BETA", name="Beta Mining Project", location="Hunter Valley, NSW", latitude=-32.73, longitude=151.55))

        # ── Zones ──────────────────────────────────────────────────────
        zone_ids = []
        for i, (code, name, site_id) in enumerate([
            ("ZONE-A1", "Excavation Zone A", site1_id),
            ("ZONE-A2", "Loading Bay", site1_id),
            ("ZONE-A3", "Haul Road North", site1_id),
            ("ZONE-B1", "Open Cut Face", site2_id),
            ("ZONE-B2", "Dump Zone", site2_id),
        ]):
            zid = uid()
            zone_ids.append(zid)
            db.add(Zone(zone_id=zid, site_id=site_id, zone_code=code, name=name,
                        speed_limit_kmh=20.0, is_restricted=(i in [0, 3])))

        # ── Machine Models ─────────────────────────────────────────────
        model_exc_id = uid()
        model_bul_id = uid()
        model_ldr_id = uid()
        db.add(MachineModel(model_id=model_exc_id, model_name="CAT 390F", machine_type="EXCAVATOR",
                            nominal_hydraulic_pressure_bar=250, fuel_tank_capacity_l=1085, max_load_tons=45, service_interval_hours=500))
        db.add(MachineModel(model_id=model_bul_id, model_name="CAT D9T", machine_type="BULLDOZER",
                            nominal_hydraulic_pressure_bar=220, fuel_tank_capacity_l=684, max_load_tons=20, service_interval_hours=500))
        db.add(MachineModel(model_id=model_ldr_id, model_name="CAT 992K", machine_type="LOADER",
                            nominal_hydraulic_pressure_bar=235, fuel_tank_capacity_l=750, max_load_tons=35, service_interval_hours=500))

        # ── Machines ───────────────────────────────────────────────────
        machine_data = [
            ("EXC001", model_exc_id, site1_id, zone_ids[0], 2019, 4821, "ACTIVE"),
            ("EXC002", model_exc_id, site1_id, zone_ids[0], 2021, 2344, "ACTIVE"),
            ("EXC003", model_exc_id, site2_id, zone_ids[3], 2020, 3612, "ACTIVE"),
            ("BUL001", model_bul_id, site1_id, zone_ids[1], 2018, 6102, "ACTIVE"),
            ("BUL002", model_bul_id, site2_id, zone_ids[3], 2022, 1205, "ACTIVE"),
            ("LDR001", model_ldr_id, site1_id, zone_ids[1], 2020, 3840, "ACTIVE"),
            ("LDR002", model_ldr_id, site2_id, zone_ids[4], 2021, 2710, "ACTIVE"),
            ("EXC004", model_exc_id, site1_id, None, 2017, 7850, "MAINTENANCE"),
            ("BUL003", model_bul_id, site1_id, None, 2023, 410, "INACTIVE"),
            ("LDR003", model_ldr_id, site2_id, None, 2019, 4920, "INACTIVE"),
        ]
        machine_ids = []
        for code, mid, sid, zid, year, hours, status in machine_data:
            m_id = uid()
            machine_ids.append(m_id)
            db.add(Machine(
                machine_id=m_id, machine_code=code, model_id=mid, site_id=sid,
                zone_id=zid, year_manufactured=year, engine_hours=hours,
                status=status, is_active=True,
                last_engine_temp_c=rng.uniform(82, 95),
                last_fuel_level_pct=rng.uniform(45, 90),
                last_machine_load_pct=rng.uniform(40, 75),
                last_speed_kmh=rng.uniform(0, 8) if status == "ACTIVE" else 0,
                last_health_score=rng.uniform(82, 97),
                last_seen=datetime.now(timezone.utc) - timedelta(minutes=rng.randint(1, 15)) if status == "ACTIVE" else None,
                authorization_status="AUTHORIZED" if status == "ACTIVE" else "PENDING",
            ))

        # ── Maintenance records ────────────────────────────────────────
        for m_id in machine_ids[:7]:
            db.add(MachineMaintenance(
                machine_id=m_id,
                maintenance_type="OIL_CHANGE",
                performed_at=datetime.now(timezone.utc) - timedelta(days=rng.randint(10, 45)),
                engine_hours_at_service=rng.uniform(200, 400),
                performed_by="Maintenance Team",
                next_service_hours=rng.uniform(400, 500),
            ))

        # ── Operators ──────────────────────────────────────────────────
        operator_names = [
            ("OP1001", "James Mitchell", 8, 4, "CAT-EXC-L3", date(2025, 11, 15), site1_id, machine_ids[0]),
            ("OP1002", "Sarah Chen", 5, 3, "CAT-EXC-L2", date(2025, 6, 30), site1_id, machine_ids[1]),
            ("OP1003", "David Williams", 12, 5, "CAT-EXC-L4", date(2026, 3, 20), site2_id, machine_ids[2]),
            ("OP1004", "Maria Garcia", 3, 2, "CAT-BUL-L1", date(2025, 9, 10), site1_id, machine_ids[3]),
            ("OP1005", "Tom Johnson", 7, 4, "CAT-BUL-L2", date(2025, 12, 5), site2_id, machine_ids[4]),
            ("OP1006", "Emily Brown", 6, 3, "CAT-LDR-L2", date(2025, 8, 22), site1_id, machine_ids[5]),
            ("OP1007", "Michael Lee", 4, 3, "CAT-LDR-L2", date(2025, 7, 14), site2_id, machine_ids[6]),
            ("OP1008", "Jessica Taylor", 10, 5, "CAT-EXC-L4", date(2026, 1, 8), site1_id, machine_ids[0]),
            ("OP1009", "Robert Davis", 2, 1, "CAT-EXC-L1", date(2025, 3, 25), site1_id, None),  # cert expiring
            ("OP1010", "Lisa Anderson", 15, 5, "CAT-SITE-MGR", date(2027, 5, 30), site2_id, None),
        ]
        operator_ids = []
        for emp_code, name, exp, skill, cert, expiry, sid, cur_machine in operator_names:
            op_id = uid()
            operator_ids.append(op_id)
            is_active = True
            shift_status = "ON_SHIFT" if emp_code in ["OP1001", "OP1002", "OP1003", "OP1004", "OP1005", "OP1006", "OP1007"] else "OFF_SHIFT"
            db.add(Operator(
                operator_id=op_id,
                employee_code=emp_code,
                name=name,
                email=f"{emp_code.lower()}@catsite.com",
                site_id=sid,
                experience_years=exp,
                skill_level=skill,
                certification=cert,
                certification_expiry=expiry,
                is_active=is_active,
                shift_status=shift_status,
                shift_start=datetime.now(timezone.utc) - timedelta(hours=rng.randint(2, 6)) if shift_status == "ON_SHIFT" else None,
                continuous_operating_minutes=rng.uniform(20, 80) if shift_status == "ON_SHIFT" else 0,
                current_machine_id=cur_machine,
                authorization_status="AUTHORIZED" if shift_status == "ON_SHIFT" else "PENDING",
                safety_score=rng.uniform(78, 98),
            ))
            # Certification record
            db.add(OperatorCertification(
                operator_id=op_id,
                cert_type="Machine Operation",
                cert_code=cert,
                issued_date=expiry - timedelta(days=365 * 2),
                expiry_date=expiry,
                issuing_body="Caterpillar Training Institute",
                is_valid=expiry >= date.today(),
            ))

        # Update machines with current operator
        for i, (_, _, _, _, _, _, _, cur_machine) in enumerate(operator_names):
            if cur_machine and i < len(operator_ids):
                pass  # machine already has current_operator_id to be set

        # Link operators to machines
        for i, m_id in enumerate(machine_ids[:7]):
            if i < len(operator_ids):
                pass  # done via Operator.current_machine_id above

        # ── Users (auth) ───────────────────────────────────────────────
        users = [
            ("engineer@cat.com", "Alex Engineer", "engineer", "demo1234", None),
            ("supervisor@cat.com", "Sam Supervisor", "supervisor", "demo1234", None),
            ("safety@cat.com", "Chris Safety", "safety_officer", "demo1234", None),
            ("admin@cat.com", "Admin User", "admin", "demo1234", None),
            ("maintenance@cat.com", "Pat Maintenance", "maintenance_engineer", "demo1234", None),
        ]
        for email, name, role, pw, op_id in users:
            db.add(User(
                user_id=uid(), email=email, name=name, role=role,
                hashed_password=hash_password(pw), is_active=True, operator_id=op_id,
            ))
        # Operator users
        for i, (emp_code, name, *_) in enumerate(operator_names):
            if i < len(operator_ids):
                db.add(User(
                    user_id=uid(),
                    email=f"{emp_code.lower()}@catsite.com",
                    name=name,
                    role="operator",
                    hashed_password=hash_password("demo1234"),
                    is_active=True,
                    operator_id=operator_ids[i],
                ))

        # ── Training Modules ───────────────────────────────────────────
        training_modules = [
            ("Proximity Safety Awareness", "SAFETY", "VIDEO", 45, True),
            ("Seatbelt & Personal Safety", "SAFETY", "VIDEO", 20, True),
            ("Fuel Efficient Operation", "MACHINE_OPERATION", "VIDEO", 30, False),
            ("Safe Operating Speeds", "MACHINE_OPERATION", "SIMULATION", 40, True),
            ("Emergency Procedures", "EMERGENCY", "VIDEO", 60, True),
            ("Excavator Advanced Operation", "MACHINE_OPERATION", "SIMULATION", 90, False),
            ("CAT 390F Machine Familiarisation", "MACHINE_OPERATION", "VIDEO", 45, True),
            ("Environmental Awareness", "ENVIRONMENT", "VIDEO", 25, True),
            ("Hazard Identification", "SAFETY", "QUIZ", 30, True),
            ("Pre-Start Inspection Procedure", "SAFETY", "VIDEO", 20, True),
        ]
        module_ids = []
        for title, cat, mtype, dur, mandatory in training_modules:
            mid = uid()
            module_ids.append(mid)
            db.add(TrainingModule(
                module_id=mid, title=title, category=cat,
                module_type=mtype, duration_minutes=dur, is_mandatory=mandatory,
            ))

        # Assign training completions to operators
        for op_id in operator_ids:
            for j, mod_id in enumerate(module_ids):
                if rng.random() > 0.3:
                    db.add(OperatorTraining(
                        operator_id=op_id,
                        module_id=mod_id,
                        status="COMPLETED",
                        completed_at=datetime.now(timezone.utc) - timedelta(days=rng.randint(10, 180)),
                        score=rng.uniform(70, 100),
                    ))

        # ── Tasks (today + recent) ─────────────────────────────────────
        task_types = ["EXCAVATION", "LOADING", "TRENCHING", "GRADING", "HAULING"]
        materials = ["CLAY", "SAND", "ROCK", "TOPSOIL", "GRAVEL"]
        task_ids = []
        now = datetime.now(timezone.utc)

        for i in range(20):
            op_idx = i % len(operator_ids)
            m_idx = i % len(machine_ids[:7])
            ttype = task_types[i % len(task_types)]
            start = now - timedelta(hours=rng.randint(1, 8))
            est_dur = rng.uniform(45, 120)
            actual_dur = est_dur * rng.uniform(0.8, 1.3)
            end = start + timedelta(minutes=actual_dur)
            status = "COMPLETED" if end < now - timedelta(minutes=10) else "IN_PROGRESS"
            qty = rng.uniform(100, 800)
            tid = uid()
            task_ids.append(tid)
            db.add(Task(
                task_id=tid,
                site_id=site1_id if i < 12 else site2_id,
                zone_id=zone_ids[i % len(zone_ids)],
                machine_id=machine_ids[m_idx],
                operator_id=operator_ids[op_idx],
                task_type=ttype,
                material_type=materials[i % len(materials)],
                target_quantity=qty,
                completed_quantity=qty if status == "COMPLETED" else qty * rng.uniform(0.3, 0.8),
                unit="m3",
                status=status,
                actual_start=start,
                actual_end=end if status == "COMPLETED" else None,
                estimated_duration_minutes=est_dur,
                actual_duration_minutes=actual_dur if status == "COMPLETED" else None,
                weather_condition=rng.choice(["CLEAR", "CLOUDY", "CLEAR", "CLEAR"]),
                terrain_type=rng.choice(["FLAT", "SLOPE", "FLAT", "ROUGH"]),
                priority=rng.choice([1, 2, 2, 3]),
            ))

        # ── Telemetry (recent, last 2 hours for active machines) ───────
        for m_id in machine_ids[:7]:
            for j in range(24):  # 24 rows, 5 min apart = 2 hours
                t = now - timedelta(minutes=j * 5)
                db.add(Telemetry(
                    timestamp=t,
                    site_id=site1_id,
                    machine_id=m_id,
                    operator_id=operator_ids[machine_ids.index(m_id) % len(operator_ids)],
                    engine_status="RUNNING",
                    engine_rpm=rng.uniform(1200, 1800),
                    engine_temperature_c=rng.uniform(82, 95),
                    oil_pressure_psi=rng.uniform(42, 62),
                    coolant_temperature_c=rng.uniform(78, 92),
                    battery_voltage=rng.uniform(13.2, 14.4),
                    fuel_level_pct=max(10, 75 - j * 0.3),
                    fuel_consumption_rate_lph=rng.uniform(10, 18),
                    fuel_used_l=j * 1.2,
                    hydraulic_pressure_bar=rng.uniform(230, 265),
                    hydraulic_temperature_c=rng.uniform(48, 62),
                    hydraulic_flow_lpm=rng.uniform(160, 200),
                    machine_speed_kmh=rng.uniform(0, 8),
                    machine_load_pct=rng.uniform(40, 80),
                    cycle_count=j * 2,
                    cycle_time_min=rng.uniform(4, 8),
                    idle_time_min=rng.uniform(0, 3),
                    operating_hours=rng.uniform(4800, 4830),
                    vibration_g=rng.uniform(0.1, 0.5),
                    seatbelt_status="FASTENED",
                    sudden_acceleration=rng.random() < 0.05,
                    sudden_braking=rng.random() < 0.03,
                ))

        # ── Wearable events ────────────────────────────────────────────
        for op_id in operator_ids[:7]:
            for j in range(12):
                t = now - timedelta(minutes=j * 10)
                db.add(WearableEvent(
                    timestamp=t,
                    operator_id=op_id,
                    heart_rate=rng.uniform(65, 95),
                    heart_rate_delta=rng.uniform(-5, 5),
                    activity_level=rng.uniform(4, 8),
                    motion_level=rng.uniform(3, 7),
                    skin_temperature_c=rng.uniform(35.5, 37.0),
                    wearable_battery_pct=rng.uniform(55, 95),
                    wearable_connected=True,
                    attention_risk_indicator=rng.uniform(0.05, 0.25),
                    fatigue_risk_indicator=rng.uniform(0.05, 0.40),
                    self_reported_status="FIT_FOR_WORK",
                ))

        # ── Alerts (recent realistic events) ──────────────────────────
        alert_scenarios = [
            ("PROXIMITY_WARNING", "MEDIUM", "Person detected at 8.2m — approaching proximity warning zone.", operator_ids[0], machine_ids[0]),
            ("SEATBELT_UNFASTENED", "HIGH", "Seatbelt unfastened while machine in motion.", operator_ids[1], machine_ids[1]),
            ("EXCESSIVE_IDLING", "LOW", "Machine idle for 18 minutes.", operator_ids[3], machine_ids[3]),
            ("ENGINE_TEMP_WARNING", "MEDIUM", "Engine temperature 107°C — approaching critical threshold.", operator_ids[2], machine_ids[2]),
        ]
        alert_ids = []
        for atype, sev, msg, op_id, m_id in alert_scenarios:
            a_id = uid()
            alert_ids.append(a_id)
            db.add(Alert(
                alert_id=a_id,
                timestamp=now - timedelta(hours=rng.randint(1, 4)),
                site_id=site1_id,
                machine_id=m_id,
                operator_id=op_id,
                alert_type=atype,
                severity=sev,
                message=msg,
                recommended_action="Review and take appropriate action.",
                trigger_data={"simulated": True},
                acknowledged=rng.random() > 0.5,
                resolved=False,
            ))

        # ── Incidents ──────────────────────────────────────────────────
        db.add(Incident(
            timestamp=now - timedelta(hours=2),
            site_id=site1_id,
            zone_id=zone_ids[0],
            machine_id=machine_ids[0],
            operator_id=operator_ids[0],
            alert_id=alert_ids[0],
            category="PROXIMITY",
            severity="MEDIUM",
            description="Worker entered EXC001 operating zone. Machine halted automatically. Worker directed to safe zone.",
            trigger_data={"person_distance_m": 4.2},
            status="INVESTIGATING",
            is_auto_created=True,
        ))

        # ── Pre-start checks ───────────────────────────────────────────
        for op_id, m_id in [(operator_ids[0], machine_ids[0]), (operator_ids[1], machine_ids[1])]:
            db.add(PrestartCheck(
                machine_id=m_id,
                operator_id=op_id,
                performed_at=now - timedelta(hours=rng.randint(3, 6)),
                items=[{"item_id": k, "passed": True} for k in
                       ["auth", "authorized", "cert_valid", "seatbelt", "fuel", "health", "no_faults", "zone_clear", "emergency", "training"]],
                authorization_status="AUTHORIZED",
                blocked_reasons=[],
                review_reasons=[],
            ))

        # ── Dashcam events ─────────────────────────────────────────────
        for i in range(5):
            db.add(DashcamEvent(
                timestamp=now - timedelta(minutes=rng.randint(10, 240)),
                camera_id=f"CAM-EXC00{rng.randint(1,3)}-FRONT",
                machine_id=machine_ids[rng.randint(0, 2)],
                operator_id=operator_ids[rng.randint(0, 6)],
                person_detected=rng.random() > 0.3,
                vehicle_detected=rng.random() > 0.6,
                obstacle_detected=rng.random() > 0.7,
                restricted_zone_entry=rng.random() > 0.8,
                estimated_distance_m=rng.uniform(3, 20),
                confidence=rng.uniform(0.75, 0.95),
                event_type="person_detected",
            ))

        # ── Environmental data ─────────────────────────────────────────
        for i in range(24):
            db.add(EnvironmentalData(
                timestamp=now - timedelta(hours=i),
                site_id=site1_id,
                temperature_c=rng.uniform(18, 28),
                humidity_pct=rng.uniform(40, 70),
                rainfall_mm=0.0,
                wind_speed_kmh=rng.uniform(5, 20),
                visibility_m=rng.uniform(5000, 10000),
                weather_condition="CLEAR",
                ground_condition="DRY",
                terrain_type="FLAT",
                dust_level="LOW",
            ))

        await db.commit()
        logger.info("Demo data seeded successfully.")
        logger.info("Login credentials: engineer@cat.com / demo1234, op1001@catsite.com / demo1234")
