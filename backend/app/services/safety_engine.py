"""
Rule-based safety engine.
Each rule is a pure function that returns an Alert dict or None.
All thresholds come from config.
"""
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.config import settings
from ..models.safety import Alert, Incident, DashcamEvent
from ..core.ws_manager import ws_manager
import logging

logger = logging.getLogger(__name__)


def _new_alert(
    alert_type: str,
    severity: str,
    message: str,
    recommended_action: str,
    trigger_data: dict,
    machine_id: str | None = None,
    operator_id: str | None = None,
    site_id: str | None = None,
    zone_id: str | None = None,
    task_id: str | None = None,
) -> Alert:
    return Alert(
        timestamp=datetime.now(timezone.utc),
        site_id=site_id,
        zone_id=zone_id,
        machine_id=machine_id,
        operator_id=operator_id,
        task_id=task_id,
        alert_type=alert_type,
        severity=severity,
        trigger_data=trigger_data,
        message=message,
        recommended_action=recommended_action,
    )


# ── Individual rules ──────────────────────────────────────────────────────────

def check_seatbelt(seatbelt_status: str, speed_kmh: float, **ctx) -> Alert | None:
    if seatbelt_status == "UNFASTENED" and speed_kmh > 0.5:
        return _new_alert(
            alert_type="SEATBELT_UNFASTENED",
            severity="HIGH",
            message="Seatbelt unfastened while machine is in motion.",
            recommended_action="Stop machine and fasten seatbelt before continuing.",
            trigger_data={"seatbelt_status": seatbelt_status, "speed_kmh": speed_kmh},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    return None


def check_proximity(person_distance_m: float, **ctx) -> Alert | None:
    if person_distance_m <= settings.proximity_critical_meters:
        return _new_alert(
            alert_type="PROXIMITY_CRITICAL",
            severity="CRITICAL",
            message=f"Person detected at {person_distance_m:.1f}m — critical proximity threshold exceeded.",
            recommended_action="Stop machine immediately. Do not move until area is clear.",
            trigger_data={"person_distance_m": person_distance_m, "threshold_m": settings.proximity_critical_meters},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    elif person_distance_m <= settings.proximity_warning_meters:
        return _new_alert(
            alert_type="PROXIMITY_WARNING",
            severity="MEDIUM",
            message=f"Person detected at {person_distance_m:.1f}m — approaching proximity warning zone.",
            recommended_action="Reduce speed and increase awareness of surroundings.",
            trigger_data={"person_distance_m": person_distance_m, "threshold_m": settings.proximity_warning_meters},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    return None


def check_speed(speed_kmh: float, speed_limit_kmh: float | None = None, **ctx) -> Alert | None:
    limit = speed_limit_kmh or settings.speed_limit_default_kmh
    if speed_kmh > limit:
        return _new_alert(
            alert_type="SPEED_VIOLATION",
            severity="HIGH",
            message=f"Machine speed {speed_kmh:.1f} km/h exceeds zone limit of {limit:.1f} km/h.",
            recommended_action="Reduce speed immediately to comply with site speed limit.",
            trigger_data={"speed_kmh": speed_kmh, "speed_limit_kmh": limit},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    return None


def check_load(load_pct: float, **ctx) -> Alert | None:
    if load_pct > settings.max_load_critical_pct:
        return _new_alert(
            alert_type="OVERLOAD_CRITICAL",
            severity="CRITICAL",
            message=f"Machine load at {load_pct:.0f}% — exceeds maximum rated capacity.",
            recommended_action="Reduce load immediately to prevent equipment damage and rollover risk.",
            trigger_data={"load_pct": load_pct, "threshold": settings.max_load_critical_pct},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    elif load_pct > settings.max_load_warning_pct:
        return _new_alert(
            alert_type="OVERLOAD_WARNING",
            severity="MEDIUM",
            message=f"Machine load at {load_pct:.0f}% — approaching maximum capacity.",
            recommended_action="Monitor load carefully. Prepare to reduce if load continues to rise.",
            trigger_data={"load_pct": load_pct, "threshold": settings.max_load_warning_pct},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    return None


def check_engine_temperature(temp_c: float, **ctx) -> Alert | None:
    if temp_c > settings.engine_temp_critical_c:
        return _new_alert(
            alert_type="ENGINE_TEMP_CRITICAL",
            severity="CRITICAL",
            message=f"Engine temperature {temp_c:.0f}°C — critical overheating. Shutdown required.",
            recommended_action="Stop machine immediately. Allow engine to cool. Do not restart until inspected.",
            trigger_data={"temp_c": temp_c, "threshold": settings.engine_temp_critical_c},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    elif temp_c > settings.engine_temp_warning_c:
        return _new_alert(
            alert_type="ENGINE_TEMP_WARNING",
            severity="MEDIUM",
            message=f"Engine temperature {temp_c:.0f}°C — approaching critical threshold.",
            recommended_action="Reduce load and monitor engine temperature. Check coolant levels.",
            trigger_data={"temp_c": temp_c, "threshold": settings.engine_temp_warning_c},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    return None


def check_hydraulic_pressure(pressure_bar: float, nominal: float = 250.0, **ctx) -> Alert | None:
    lower = nominal * 0.8
    upper = nominal * 1.2
    if pressure_bar < lower or pressure_bar > upper:
        return _new_alert(
            alert_type="HYDRAULIC_WARNING",
            severity="MEDIUM",
            message=f"Hydraulic pressure {pressure_bar:.0f} bar — outside normal operating range ({lower:.0f}–{upper:.0f} bar).",
            recommended_action="Reduce operating load. Inspect hydraulic system for leaks or blockages.",
            trigger_data={"pressure_bar": pressure_bar, "nominal_bar": nominal, "range": [lower, upper]},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    return None


def check_idle_time(idle_minutes: float, **ctx) -> Alert | None:
    if idle_minutes > settings.max_idle_minutes:
        return _new_alert(
            alert_type="EXCESSIVE_IDLING",
            severity="LOW",
            message=f"Machine has been idle for {idle_minutes:.0f} minutes — exceeds {settings.max_idle_minutes:.0f} minute threshold.",
            recommended_action="Investigate cause of idle. Shut down machine if extended idle expected.",
            trigger_data={"idle_minutes": idle_minutes, "threshold": settings.max_idle_minutes},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    return None


def check_break_needed(continuous_operating_minutes: float, **ctx) -> Alert | None:
    if continuous_operating_minutes > settings.max_continuous_operating_minutes:
        return _new_alert(
            alert_type="BREAK_RECOMMENDATION",
            severity="LOW",
            message=f"Operator has been operating continuously for {continuous_operating_minutes:.0f} minutes. A break is recommended.",
            recommended_action="Schedule a rest break. Fatigue increases risk of accidents.",
            trigger_data={"continuous_minutes": continuous_operating_minutes, "threshold": settings.max_continuous_operating_minutes},
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    return None


def check_fatigue_risk(fatigue_risk_indicator: float, **ctx) -> Alert | None:
    """
    Fatigue risk indicator — operational risk indicator only.
    NOT a medical diagnosis. Derived from wearable motion/activity patterns.
    """
    if fatigue_risk_indicator > settings.fatigue_risk_threshold:
        return _new_alert(
            alert_type="FATIGUE_RISK",
            severity="MEDIUM",
            message=f"Elevated fatigue risk indicator detected ({fatigue_risk_indicator:.2f}). "
                    "Note: This is an operational risk indicator — not a medical assessment.",
            recommended_action="Supervisor review recommended. Consider scheduling a break.",
            trigger_data={
                "fatigue_risk_indicator": fatigue_risk_indicator,
                "threshold": settings.fatigue_risk_threshold,
                "disclaimer": "Operational risk indicator — not a medical diagnosis",
            },
            **{k: v for k, v in ctx.items() if k in ("machine_id", "operator_id", "site_id", "zone_id", "task_id")},
        )
    return None


# ── Safety Engine orchestrator ────────────────────────────────────────────────

class SafetyEngine:
    async def evaluate_telemetry(self, telemetry_data: dict, db: AsyncSession) -> list[Alert]:
        """
        Evaluate a telemetry snapshot against all rules.
        Returns list of created Alert ORM objects.
        """
        ctx = {
            "machine_id": telemetry_data.get("machine_id"),
            "operator_id": telemetry_data.get("operator_id"),
            "site_id": telemetry_data.get("site_id"),
            "zone_id": telemetry_data.get("zone_id"),
            "task_id": telemetry_data.get("task_id"),
        }

        triggered: list[Alert] = []

        rules_results = [
            check_seatbelt(
                telemetry_data.get("seatbelt_status", "FASTENED"),
                telemetry_data.get("machine_speed_kmh", 0),
                **ctx,
            ),
            check_speed(
                telemetry_data.get("machine_speed_kmh", 0),
                telemetry_data.get("speed_limit_kmh"),
                **ctx,
            ),
            check_load(telemetry_data.get("machine_load_pct", 0), **ctx),
            check_idle_time(telemetry_data.get("idle_time_min", 0), **ctx),
        ]
        if telemetry_data.get("engine_temperature_c"):
            rules_results.append(check_engine_temperature(telemetry_data["engine_temperature_c"], **ctx))
        if telemetry_data.get("hydraulic_pressure_bar"):
            rules_results.append(check_hydraulic_pressure(telemetry_data["hydraulic_pressure_bar"], **ctx))
        if telemetry_data.get("person_distance_m"):
            rules_results.append(check_proximity(telemetry_data["person_distance_m"], **ctx))
        if telemetry_data.get("continuous_operating_minutes"):
            rules_results.append(check_break_needed(telemetry_data["continuous_operating_minutes"], **ctx))
        if telemetry_data.get("fatigue_risk_indicator"):
            rules_results.append(check_fatigue_risk(telemetry_data["fatigue_risk_indicator"], **ctx))

        for alert in rules_results:
            if alert is not None:
                db.add(alert)
                triggered.append(alert)

        if triggered:
            await db.flush()
            # Broadcast each alert
            for alert in triggered:
                await ws_manager.broadcast_alert({
                    "alert_id": alert.alert_id,
                    "timestamp": alert.timestamp.isoformat(),
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "recommended_action": alert.recommended_action,
                    "machine_id": alert.machine_id,
                    "operator_id": alert.operator_id,
                    "acknowledged": False,
                    "trigger_data": alert.trigger_data,
                })
                # Auto-create incident for CRITICAL alerts
                if alert.severity == "CRITICAL":
                    incident = Incident(
                        timestamp=datetime.now(timezone.utc),
                        site_id=alert.site_id,
                        zone_id=alert.zone_id,
                        machine_id=alert.machine_id,
                        operator_id=alert.operator_id,
                        alert_id=alert.alert_id,
                        category=alert.alert_type.split("_")[0],
                        severity="HIGH",
                        description=f"Auto-created from CRITICAL alert: {alert.message}",
                        trigger_data=alert.trigger_data,
                        status="OPEN",
                        is_auto_created=True,
                    )
                    db.add(incident)

        return triggered

    async def evaluate_cv_event(self, cv_event: DashcamEvent, db: AsyncSession) -> list[Alert]:
        """Evaluate a dashcam CV event and trigger proximity/zone alerts."""
        ctx = {
            "machine_id": cv_event.machine_id,
            "operator_id": cv_event.operator_id,
        }
        triggered = []

        if cv_event.person_detected and cv_event.estimated_distance_m is not None:
            alert = check_proximity(cv_event.estimated_distance_m, **ctx)
            if alert:
                alert.alert_type = f"DASHCAM_{alert.alert_type}"
                db.add(alert)
                triggered.append(alert)
                cv_event.alert_id = alert.alert_id

        if cv_event.restricted_zone_entry:
            alert = _new_alert(
                alert_type="DASHCAM_PERSON_ZONE",
                severity="HIGH",
                message="Person detected inside restricted operating zone.",
                recommended_action="Stop machine. Clear the zone before resuming.",
                trigger_data={"camera_id": cv_event.camera_id, "event_type": cv_event.event_type},
                **ctx,
            )
            db.add(alert)
            triggered.append(alert)

        if triggered:
            await db.flush()
            for alert in triggered:
                await ws_manager.broadcast_alert({
                    "alert_id": alert.alert_id,
                    "timestamp": alert.timestamp.isoformat(),
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "recommended_action": alert.recommended_action,
                    "machine_id": alert.machine_id,
                    "operator_id": alert.operator_id,
                    "acknowledged": False,
                    "trigger_data": alert.trigger_data,
                })

        return triggered
