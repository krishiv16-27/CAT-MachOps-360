"""
Operator safety score computation.
Score is a weighted composite — labelled 'Operational Safety Score (Demo Index)'.
"""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..core.config import settings
from ..models.safety import Alert, Incident, PrestartCheck
from ..models.training import OperatorTraining, TrainingModule
import logging

logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 7


async def compute_operator_safety_score(operator_id: str, db: AsyncSession) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    # 1. Seatbelt compliance
    seatbelt_events = (await db.execute(
        select(func.count()).where(
            Alert.operator_id == operator_id,
            Alert.alert_type == "SEATBELT_UNFASTENED",
            Alert.timestamp >= since,
        )
    )).scalar() or 0
    # Score: 100 - 10 per event, min 0
    seatbelt_score = max(0.0, 100.0 - seatbelt_events * 15)

    # 2. Proximity events
    proximity_events = (await db.execute(
        select(func.count()).where(
            Alert.operator_id == operator_id,
            Alert.alert_type.in_(["PROXIMITY_WARNING", "PROXIMITY_CRITICAL", "DASHCAM_PROXIMITY_CRITICAL", "DASHCAM_PROXIMITY_WARNING"]),
            Alert.timestamp >= since,
        )
    )).scalar() or 0
    proximity_score = max(0.0, 100.0 - proximity_events * 10)

    # 3. Speed violations
    speed_events = (await db.execute(
        select(func.count()).where(
            Alert.operator_id == operator_id,
            Alert.alert_type == "SPEED_VIOLATION",
            Alert.timestamp >= since,
        )
    )).scalar() or 0
    speed_score = max(0.0, 100.0 - speed_events * 12)

    # 4. Incidents
    incident_count = (await db.execute(
        select(func.count()).where(
            Incident.operator_id == operator_id,
            Incident.timestamp >= since,
        )
    )).scalar() or 0
    incident_score = max(0.0, 100.0 - incident_count * 20)

    # 5. Pre-start compliance (proportion passed vs blocked in last 30 days)
    total_checks = (await db.execute(
        select(func.count()).where(PrestartCheck.operator_id == operator_id)
    )).scalar() or 0
    passed_checks = (await db.execute(
        select(func.count()).where(
            PrestartCheck.operator_id == operator_id,
            PrestartCheck.authorization_status == "AUTHORIZED",
        )
    )).scalar() or 0
    prestart_score = (passed_checks / max(total_checks, 1)) * 100

    # 6. Training completion
    total_mandatory = (await db.execute(
        select(func.count()).where(TrainingModule.is_mandatory == True, TrainingModule.is_active == True)
    )).scalar() or 1
    completed_mandatory = (await db.execute(
        select(func.count()).select_from(OperatorTraining).join(
            TrainingModule, OperatorTraining.module_id == TrainingModule.module_id
        ).where(
            OperatorTraining.operator_id == operator_id,
            OperatorTraining.status == "COMPLETED",
            TrainingModule.is_mandatory == True,
        )
    )).scalar() or 0
    training_score = (completed_mandatory / max(total_mandatory, 1)) * 100

    s = settings
    overall = (
        seatbelt_score * s.safety_weight_seatbelt
        + proximity_score * s.safety_weight_proximity
        + speed_score * s.safety_weight_speed
        + incident_score * s.safety_weight_incident
        + prestart_score * s.safety_weight_prestart
        + training_score * s.safety_weight_training
    )

    return {
        "overall": round(overall, 1),
        "label": "Operational Safety Score (Demo Index)",
        "components": {
            "seatbelt_compliance": {
                "score": round(seatbelt_score, 1),
                "weight": s.safety_weight_seatbelt,
                "events_count": seatbelt_events,
            },
            "proximity_events": {
                "score": round(proximity_score, 1),
                "weight": s.safety_weight_proximity,
                "events_count": proximity_events,
            },
            "speed_violations": {
                "score": round(speed_score, 1),
                "weight": s.safety_weight_speed,
                "events_count": speed_events,
            },
            "incident_rate": {
                "score": round(incident_score, 1),
                "weight": s.safety_weight_incident,
                "incidents_count": incident_count,
            },
            "prestart_compliance": {
                "score": round(prestart_score, 1),
                "weight": s.safety_weight_prestart,
            },
            "training_completion": {
                "score": round(training_score, 1),
                "weight": s.safety_weight_training,
                "pending_modules": max(0, total_mandatory - completed_mandatory),
            },
        },
        "lookback_days": LOOKBACK_DAYS,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }
