"""
Silent Risk Detection Service.
Monitors combinations of weak signals over the last 30 minutes of telemetry
to detect composite risk patterns before any single threshold is breached.
"""
from datetime import datetime, timezone, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

logger = logging.getLogger(__name__)


def _trend(values: list[float]) -> float:
    """Simple linear trend: positive = rising, negative = falling."""
    if len(values) < 2:
        return 0.0
    n = len(values)
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    num = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    return num / den if den else 0.0


async def get_silent_risk(machine_id: str, db: AsyncSession) -> dict:
    from ..models.telemetry import Telemetry
    from ..models.machine import Machine

    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=30)

    mach_result = await db.execute(select(Machine).where(Machine.machine_id == machine_id))
    mach = mach_result.scalar_one_or_none()

    telem_result = await db.execute(
        select(Telemetry)
        .where(Telemetry.machine_id == machine_id, Telemetry.timestamp >= window_start)
        .order_by(Telemetry.timestamp)
        .limit(60)
    )
    rows = telem_result.scalars().all()

    patterns = []
    composite_score = 0

    if len(rows) < 5:
        # Not enough data — use mock signals for demo
        rows_data = _mock_telemetry_signals(machine_id)
    else:
        rows_data = {
            "engine_temps": [r.engine_temperature_c for r in rows if r.engine_temperature_c],
            "fuel_rates": [r.fuel_consumption_rate_lph for r in rows if r.fuel_consumption_rate_lph],
            "hydraulic_temps": [getattr(r, "hydraulic_temperature_c", None) for r in rows],
            "hydraulic_pressures": [r.hydraulic_pressure_bar for r in rows if r.hydraulic_pressure_bar],
            "cycle_times": [r.cycle_time_min for r in rows if r.cycle_time_min and r.cycle_time_min > 0],
            "idle_times": [r.idle_time_min for r in rows if r.idle_time_min],
            "speeds": [r.machine_speed_kmh for r in rows if r.machine_speed_kmh is not None],
            "loads": [r.machine_load_pct for r in rows if r.machine_load_pct],
        }

    et = rows_data["engine_temps"]
    fr = rows_data["fuel_rates"]
    ht = [x for x in rows_data.get("hydraulic_temps", []) if x is not None]
    hp = rows_data["hydraulic_pressures"]
    ct = rows_data["cycle_times"]
    it = rows_data["idle_times"]
    sp = rows_data["speeds"]
    ld = rows_data["loads"]

    # ── Pattern 1: Emerging thermal load (engine + fuel + cycles all rising) ──
    p1_score = 0
    if len(et) >= 5 and len(fr) >= 5:
        et_trend = _trend(et[-10:])
        fr_trend = _trend(fr[-10:])
        ct_trend = _trend(ct[-8:]) if len(ct) >= 8 else 0
        if et_trend > 0.05 and fr_trend > 0.02:
            p1_score = min(100, int((et_trend * 400 + fr_trend * 600 + abs(ct_trend) * 200)))
        if p1_score >= 40:
            patterns.append({
                "pattern": "THERMAL_LOAD",
                "label": "Emerging thermal load pattern",
                "description": (
                    f"Engine temperature trending +{et_trend:.3f}°C/min and fuel consumption rising. "
                    f"No threshold breached yet, but trajectory warrants monitoring."
                ),
                "score": p1_score,
                "signals": {
                    "engine_temp_trend": round(et_trend, 4),
                    "fuel_rate_trend": round(fr_trend, 4),
                    "cycle_time_trend": round(ct_trend, 4),
                },
            })
            composite_score = max(composite_score, p1_score)

    # ── Pattern 2: Hydraulic system stress (pressure dropping, load rising) ──
    p2_score = 0
    if len(hp) >= 5:
        hp_trend = _trend(hp[-10:])
        ld_trend = _trend(ld[-10:]) if len(ld) >= 10 else 0
        if hp_trend < -0.3 and ld_trend > 0.1:
            p2_score = min(100, int(abs(hp_trend) * 80 + ld_trend * 60))
        if p2_score >= 40:
            patterns.append({
                "pattern": "HYDRAULIC_STRESS",
                "label": "Possible hydraulic system stress",
                "description": (
                    f"Hydraulic pressure declining ({hp_trend:.2f} bar/min) while load increases. "
                    "Possible pump fatigue or developing leak."
                ),
                "score": p2_score,
                "signals": {
                    "hydraulic_pressure_trend": round(hp_trend, 4),
                    "load_trend": round(ld_trend, 4),
                },
            })
            composite_score = max(composite_score, p2_score)

    # ── Pattern 3: Unusual inactivity ─────────────────────────────────────────
    p3_score = 0
    if it:
        avg_idle = sum(it) / len(it)
        recent_idle = sum(it[-10:]) / len(it[-10:]) if len(it) >= 10 else avg_idle
        zero_speed_count = sum(1 for s in sp[-10:] if s is not None and s < 0.5) if len(sp) >= 10 else 0
        if avg_idle > 4 and recent_idle > avg_idle * 1.8 and zero_speed_count > 7:
            p3_score = min(100, int(avg_idle * 6 + zero_speed_count * 4))
        if p3_score >= 40:
            patterns.append({
                "pattern": "UNUSUAL_INACTIVITY",
                "label": "Unusual inactivity pattern",
                "description": (
                    f"Idle time {recent_idle:.1f} min/reading — above operator's typical baseline. "
                    "Machine stationary for extended period. Possible equipment issue or operator fatigue."
                ),
                "score": p3_score,
                "signals": {
                    "avg_idle_min": round(avg_idle, 2),
                    "recent_idle_min": round(recent_idle, 2),
                    "zero_speed_readings": zero_speed_count,
                },
            })
            composite_score = max(composite_score, p3_score)

    # Overall risk level
    if composite_score >= 80:
        risk_level = "HIGH"
    elif composite_score >= 60:
        risk_level = "MEDIUM"
    elif composite_score >= 40:
        risk_level = "LOW"
    else:
        risk_level = "NONE"

    return {
        "machine_id": machine_id,
        "machine_code": mach.machine_code if mach else machine_id,
        "composite_score": composite_score,
        "risk_level": risk_level,
        "patterns": patterns,
        "telemetry_window_minutes": 30,
        "telemetry_rows_analysed": len(rows),
        "message": _risk_message(risk_level, patterns),
        "computed_at": now.isoformat(),
    }


def _risk_message(level: str, patterns: list) -> str:
    if level == "NONE":
        return "No composite risk patterns detected. All signal combinations within normal bounds."
    if level == "LOW":
        first = patterns[0]["label"] if patterns else "minor signals"
        return f"Low-level risk pattern: {first}. Monitor over next 15 minutes."
    if level == "MEDIUM":
        names = " + ".join(p["label"] for p in patterns[:2])
        return f"Composite risk pattern detected: {names}. No single threshold exceeded but multiple indicators trending."
    return f"High composite risk — {len(patterns)} pattern(s) converging. Recommend load reduction and inspection."


def _mock_telemetry_signals(machine_id: str) -> dict:
    """Return mock signals for demo when insufficient real telemetry exists."""
    import random
    rng = random.Random(hash(machine_id) % 99999)
    n = 30
    base_temp = rng.uniform(85, 95)
    base_fuel = rng.uniform(10, 14)
    base_hp = rng.uniform(235, 260)
    return {
        "engine_temps": [base_temp + i * rng.uniform(0.0, 0.25) for i in range(n)],
        "fuel_rates": [base_fuel + i * rng.uniform(-0.02, 0.08) for i in range(n)],
        "hydraulic_temps": [42 + i * rng.uniform(-0.1, 0.3) for i in range(n)],
        "hydraulic_pressures": [base_hp + rng.uniform(-15, 15) for _ in range(n)],
        "cycle_times": [rng.uniform(5, 8) for _ in range(n)],
        "idle_times": [rng.uniform(0, 2) for _ in range(n)],
        "speeds": [rng.uniform(0, 8) for _ in range(n)],
        "loads": [rng.uniform(40, 75) for _ in range(n)],
    }
