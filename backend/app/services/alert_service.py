"""Alert service helpers used by WebSocket manager."""
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


async def acknowledge_alert_ws(alert_id: str | None, client_id: str, note: str | None = None):
    """Called from WebSocket manager to acknowledge an alert."""
    if not alert_id:
        return
    # Import here to avoid circular imports at module level
    from ..core.database import AsyncSessionLocal
    from ..models.safety import Alert
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Alert).where(Alert.alert_id == alert_id))
        alert = result.scalar_one_or_none()
        if alert:
            alert.acknowledged = True
            alert.acknowledged_at = datetime.now(timezone.utc)
            alert.acknowledgement_note = note
            await db.commit()
            logger.info(f"Alert {alert_id} acknowledged via WebSocket by client {client_id}")
