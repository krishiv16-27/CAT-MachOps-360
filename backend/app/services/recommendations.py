"""
Rule-based training recommendation engine.
No ML — deterministic rules based on operator event history.
"""
from datetime import datetime, timezone, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from ..models.safety import Alert
from ..models.operator import Operator
from ..models.training import TrainingRecommendation, TrainingModule
import logging

logger = logging.getLogger(__name__)

LOOKBACK_DAYS = 7


async def get_recommendations(operator_id: str, db: AsyncSession) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS)
    recommendations = []

    # 1. Proximity events > 3 in last 7 days
    proximity_count = (await db.execute(
        select(func.count()).where(
            Alert.operator_id == operator_id,
            Alert.alert_type.in_(["PROXIMITY_WARNING", "PROXIMITY_CRITICAL"]),
            Alert.timestamp >= since,
        )
    )).scalar() or 0

    if proximity_count >= 3:
        recommendations.append({
            "trigger_type": "PROXIMITY_EVENTS",
            "title": "Proximity Safety Awareness",
            "reason": f"{proximity_count} proximity alerts in the last {LOOKBACK_DAYS} days. Review safe operating distances.",
            "priority": "HIGH",
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
        })

    # 2. Excessive idling > 5 alerts
    idle_count = (await db.execute(
        select(func.count()).where(
            Alert.operator_id == operator_id,
            Alert.alert_type == "EXCESSIVE_IDLING",
            Alert.timestamp >= since,
        )
    )).scalar() or 0

    if idle_count >= 3:
        recommendations.append({
            "trigger_type": "EXCESSIVE_IDLE",
            "title": "Fuel Efficient Operation",
            "reason": f"{idle_count} excessive idle alerts recorded. Review efficient machine operation techniques.",
            "priority": "MEDIUM",
            "due_date": (date.today() + timedelta(days=14)).isoformat(),
        })

    # 3. Speed violations > 2
    speed_count = (await db.execute(
        select(func.count()).where(
            Alert.operator_id == operator_id,
            Alert.alert_type == "SPEED_VIOLATION",
            Alert.timestamp >= since,
        )
    )).scalar() or 0

    if speed_count >= 2:
        recommendations.append({
            "trigger_type": "SPEED_VIOLATIONS",
            "title": "Safe Operating Speeds",
            "reason": f"{speed_count} speed violations recorded. Review site speed limits and safe operating practices.",
            "priority": "HIGH",
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
        })

    # 4. Certification expiring within 30 days
    op_result = await db.execute(select(Operator).where(Operator.operator_id == operator_id))
    op = op_result.scalar_one_or_none()
    if op and op.certification_expiry:
        days_until_expiry = (op.certification_expiry - date.today()).days
        if 0 < days_until_expiry <= 30:
            recommendations.append({
                "trigger_type": "CERT_EXPIRING",
                "title": "Certification Renewal",
                "reason": f"Certification '{op.certification}' expires in {days_until_expiry} days.",
                "priority": "HIGH",
                "due_date": op.certification_expiry.isoformat(),
            })
        elif days_until_expiry <= 0:
            recommendations.append({
                "trigger_type": "CERT_EXPIRED",
                "title": "Certification Renewal — URGENT",
                "reason": f"Certification '{op.certification}' has expired. Cannot authorize machine operation.",
                "priority": "CRITICAL",
                "due_date": date.today().isoformat(),
            })

    # 5. Seatbelt violations
    seatbelt_count = (await db.execute(
        select(func.count()).where(
            Alert.operator_id == operator_id,
            Alert.alert_type == "SEATBELT_UNFASTENED",
            Alert.timestamp >= since,
        )
    )).scalar() or 0

    if seatbelt_count >= 2:
        recommendations.append({
            "trigger_type": "SEATBELT_VIOLATIONS",
            "title": "Seatbelt & Personal Safety",
            "reason": f"{seatbelt_count} seatbelt alerts recorded. Review mandatory PPE and seatbelt requirements.",
            "priority": "HIGH",
            "due_date": (date.today() + timedelta(days=3)).isoformat(),
        })

    return recommendations
