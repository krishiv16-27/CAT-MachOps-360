"""
Demo scenario simulator.
Injects realistic telemetry/events for each demo scenario.
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.machine import Machine
from ..models.operator import Operator
from ..models.telemetry import Telemetry
from ..models.safety import Alert, DashcamEvent
from ..models.task import Task
from ..services.safety_engine import SafetyEngine
from ..core.ws_manager import ws_manager
import logging

logger = logging.getLogger(__name__)


class SimulatorService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.engine = SafetyEngine()

    async def _get_demo_machine(self, machine_id: str | None) -> Machine | None:
        if machine_id:
            result = await self.db.execute(select(Machine).where(Machine.machine_id == machine_id))
            return result.scalar_one_or_none()
        result = await self.db.execute(select(Machine).where(Machine.is_active == True).limit(1))
        return result.scalar_one_or_none()

    async def _get_demo_operator(self, operator_id: str | None) -> Operator | None:
        if operator_id:
            result = await self.db.execute(select(Operator).where(Operator.operator_id == operator_id))
            return result.scalar_one_or_none()
        result = await self.db.execute(select(Operator).where(Operator.is_active == True).limit(1))
        return result.scalar_one_or_none()

    async def activate(self, scenario: str, machine_id: str | None = None, operator_id: str | None = None) -> dict:
        machine = await self._get_demo_machine(machine_id)
        operator = await self._get_demo_operator(operator_id)

        mid = machine.machine_id if machine else "DEMO_MACHINE"
        oid = operator.operator_id if operator else None
        sid = machine.site_id if machine else None

        ts = datetime.now(timezone.utc)
        scenario_upper = scenario.upper()
        events_injected = 0

        if scenario_upper == "PROXIMITY_HAZARD":
            telem = {"machine_id": mid, "operator_id": oid, "site_id": sid,
                     "machine_speed_kmh": 3.0, "seatbelt_status": "FASTENED",
                     "machine_load_pct": 50, "idle_time_min": 0,
                     "person_distance_m": 3.5}
            alerts = await self.engine.evaluate_telemetry(telem, self.db)
            events_injected = len(alerts)
            description = f"Person detected at 3.5m from {machine.machine_code if machine else 'DEMO'}. CRITICAL proximity alert fired."

        elif scenario_upper == "SEATBELT_VIOLATION":
            telem = {"machine_id": mid, "operator_id": oid, "site_id": sid,
                     "machine_speed_kmh": 8.0, "seatbelt_status": "UNFASTENED",
                     "machine_load_pct": 40, "idle_time_min": 0}
            alerts = await self.engine.evaluate_telemetry(telem, self.db)
            events_injected = len(alerts)
            description = "Seatbelt unfastened while machine moving at 8 km/h. HIGH alert fired."

        elif scenario_upper == "EXCESSIVE_IDLING":
            telem = {"machine_id": mid, "operator_id": oid, "site_id": sid,
                     "machine_speed_kmh": 0, "seatbelt_status": "FASTENED",
                     "machine_load_pct": 0, "idle_time_min": 25}
            alerts = await self.engine.evaluate_telemetry(telem, self.db)
            events_injected = len(alerts)
            description = "Machine idle for 25 minutes. Excessive idling alert fired."

        elif scenario_upper == "MACHINE_OVERHEATING":
            telem = {"machine_id": mid, "operator_id": oid, "site_id": sid,
                     "machine_speed_kmh": 2.0, "seatbelt_status": "FASTENED",
                     "machine_load_pct": 95, "idle_time_min": 0,
                     "engine_temperature_c": 118.0}
            alerts = await self.engine.evaluate_telemetry(telem, self.db)
            events_injected = len(alerts)
            description = f"Engine temperature 118°C. CRITICAL overheating alert fired."
            if machine:
                machine.last_engine_temp_c = 118.0

        elif scenario_upper == "HYDRAULIC_ANOMALY":
            telem = {"machine_id": mid, "operator_id": oid, "site_id": sid,
                     "machine_speed_kmh": 1.0, "seatbelt_status": "FASTENED",
                     "machine_load_pct": 60, "idle_time_min": 0,
                     "hydraulic_pressure_bar": 145.0}
            alerts = await self.engine.evaluate_telemetry(telem, self.db)
            events_injected = len(alerts)
            description = "Hydraulic pressure dropped to 145 bar (nominal 250 bar). MEDIUM alert fired."

        elif scenario_upper == "UNUSUAL_OPERATOR_BEHAVIOUR":
            # Insert anomalous telemetry rows
            for i in range(5):
                t = Telemetry(
                    timestamp=ts,
                    site_id=sid,
                    machine_id=mid,
                    operator_id=oid,
                    engine_status="RUNNING",
                    engine_rpm=1800,
                    idle_time_min=35.0,
                    machine_speed_kmh=0,
                    machine_load_pct=0,
                    sudden_acceleration=True,
                    seatbelt_status="FASTENED",
                )
                self.db.add(t)
            await self.db.flush()
            events_injected = 5
            description = "Anomalous operating pattern injected — extended idle + repeated sudden acceleration events."
            await ws_manager.broadcast({
                "type": "OPERATOR_UPDATE",
                "payload": {
                    "operator_id": oid,
                    "anomaly_label": "UNUSUAL",
                    "anomaly_reason": "Idle duration (35 min) significantly above normal range. Repeated sudden acceleration events.",
                    "continuous_operating_minutes": 95,
                },
            })

        elif scenario_upper == "EXTENDED_SHIFT":
            telem = {"machine_id": mid, "operator_id": oid, "site_id": sid,
                     "machine_speed_kmh": 3.0, "seatbelt_status": "FASTENED",
                     "machine_load_pct": 50, "idle_time_min": 0,
                     "continuous_operating_minutes": 110}
            alerts = await self.engine.evaluate_telemetry(telem, self.db)
            events_injected = len(alerts)
            description = "Operator has been operating for 110 minutes continuously. Break recommendation alert fired."
            if operator:
                operator.continuous_operating_minutes = 110

        elif scenario_upper == "DASHCAM_PERSON_DETECTION":
            cv_event = DashcamEvent(
                timestamp=ts,
                camera_id=f"CAM-{machine.machine_code if machine else 'DEMO'}-FRONT",
                machine_id=mid,
                operator_id=oid,
                person_detected=True,
                restricted_zone_entry=True,
                estimated_distance_m=3.8,
                confidence=0.91,
                event_type="person_detected",
                raw_metadata={"source": "simulated_scenario", "scenario": "DASHCAM_PERSON_DETECTION"},
            )
            self.db.add(cv_event)
            await self.db.flush()
            alerts = await self.engine.evaluate_cv_event(cv_event, self.db)
            events_injected = len(alerts)
            description = "CV event: Person detected at 3.8m in restricted zone. CRITICAL alert + incident created."

        elif scenario_upper == "PRESTART_FAILURE":
            description = "Pre-start scenario: certification expired flag set. Next pre-start check will return BLOCKED."
            if operator:
                from datetime import date, timedelta
                operator.certification_expiry = date.today() - timedelta(days=30)
            events_injected = 0

        elif scenario_upper == "MAINTENANCE_WARNING":
            from ..models.machine import MachineFault
            fault = MachineFault(
                machine_id=mid,
                fault_code="E-HYD-042",
                fault_description="Hydraulic filter service overdue. Pressure differential above threshold.",
                severity="MEDIUM",
                detected_at=ts,
                is_active=True,
            )
            self.db.add(fault)
            await self.db.flush()
            events_injected = 1
            description = "Maintenance fault injected: E-HYD-042 — hydraulic filter service overdue."

        elif scenario_upper == "TASK_DELAY_WEATHER":
            tasks_result = await self.db.execute(
                select(Task).where(Task.status == "IN_PROGRESS").limit(1)
            )
            task = tasks_result.scalar_one_or_none()
            if task:
                task.weather_condition = "HEAVY_RAIN"
                task.delay_reason = "Heavy rainfall — terrain too wet for safe operation"
                if task.estimated_duration_minutes:
                    task.predicted_duration_minutes = task.estimated_duration_minutes * 1.35
            events_injected = 1
            description = "Heavy rain weather condition injected. Active task ETA increased by 35%."

        else:  # NORMAL_OPERATION
            description = "Simulator reset to normal operating conditions."
            events_injected = 0

        await self.db.flush()

        # Broadcast scenario activation
        await ws_manager.broadcast_scenario(scenario_upper, description, mid, oid)

        return {
            "scenario": scenario_upper,
            "description": description,
            "machine_id": mid,
            "operator_id": oid,
            "events_injected": events_injected,
            "activated_at": ts.isoformat(),
        }

    async def reset(self):
        await ws_manager.broadcast({
            "type": "SCENARIO_ACTIVATED",
            "payload": {
                "scenario": "NORMAL_OPERATION",
                "description": "Simulator reset to normal operation.",
                "activated_at": datetime.now(timezone.utc).isoformat(),
            },
        })
