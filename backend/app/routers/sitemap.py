"""
Live Site Map router.
GET  /api/v1/sitemap         — current positions of all machines + workers
POST /api/v1/sitemap/update  — trigger a WebSocket SITE_MAP_UPDATE broadcast
"""
import math
import random
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..core.dependencies import get_current_user, require_role
from ..core.ws_manager import ws_manager
from ..models.machine import Machine
from ..models.operator import Operator
from ..schemas.common import ApiResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Deterministic position seeds ─────────────────────────────────────────────
# Site canvas: 0–1000 units wide, 0–700 units tall
CANVAS_W = 1000
CANVAS_H = 700

# Named zones (x, y, w, h, type, label)
ZONES = [
    {"id": "z1", "x": 50,  "y": 50,  "w": 280, "h": 200, "type": "EXCAVATION",  "label": "Excavation Zone A"},
    {"id": "z2", "x": 400, "y": 50,  "w": 200, "h": 150, "type": "LOADING_BAY", "label": "Loading Bay 1"},
    {"id": "z3", "x": 700, "y": 50,  "w": 250, "h": 150, "type": "RESTRICTED",  "label": "Restricted Zone"},
    {"id": "z4", "x": 50,  "y": 320, "w": 350, "h": 180, "type": "HAUL_ROAD",   "label": "Main Haul Road"},
    {"id": "z5", "x": 480, "y": 280, "w": 200, "h": 160, "type": "DUMP_ZONE",   "label": "Dump Zone B"},
    {"id": "z6", "x": 740, "y": 260, "w": 210, "h": 180, "type": "SAFE_AREA",   "label": "Safe Assembly Area"},
    {"id": "z7", "x": 50,  "y": 560, "w": 250, "h": 110, "type": "WORKSHOP",    "label": "Workshop"},
    {"id": "z8", "x": 380, "y": 510, "w": 180, "h": 120, "type": "FUEL_STATION","label": "Fuel Station"},
]

# Machine home positions (seeded, deterministic)
MACHINE_HOME_POSITIONS = {
    0: (130, 120), 1: (200, 140), 2: (100, 180),
    3: (760, 580),  # EXC004 in maintenance → workshop area
    4: (80, 370),  5: (150, 390),
    6: (450, 110), 7: (480, 130),
    8: (550, 320), 9: (260, 540),
}


def _machine_pos(idx: int, status: str, time_seed: int) -> tuple[float, float]:
    """Slowly drift active machines from home position."""
    hx, hy = MACHINE_HOME_POSITIONS.get(idx, (400, 350))
    if status != "ACTIVE":
        return (float(hx), float(hy))
    rng = random.Random(time_seed + idx * 137)
    drift_x = rng.uniform(-25, 25)
    drift_y = rng.uniform(-20, 20)
    return (
        max(30, min(CANVAS_W - 30, hx + drift_x)),
        max(30, min(CANVAS_H - 30, hy + drift_y)),
    )


def _generate_workers(machine_positions: list[dict], time_seed: int) -> list[dict]:
    """Generate 18 simulated workers, 90% in safe zones, 10% near machines."""
    rng = random.Random(time_seed)
    workers = []

    # Safe-zone wanderers (16 workers)
    safe_zone = ZONES[5]  # Safe Assembly Area
    for i in range(16):
        wx = rng.uniform(safe_zone["x"] + 15, safe_zone["x"] + safe_zone["w"] - 15)
        wy = rng.uniform(safe_zone["y"] + 15, safe_zone["y"] + safe_zone["h"] - 15)
        workers.append({
            "worker_id": f"W{i+1:03d}",
            "label": f"Worker {i+1}",
            "x": round(wx, 1),
            "y": round(wy, 1),
            "zone": "SAFE_AREA",
            "proximity_status": "SAFE",
        })

    # Near-machine workers (2 workers)
    for j in range(2):
        if machine_positions:
            m = rng.choice(machine_positions[:5])  # near active machines only
            offset_x = rng.uniform(12, 22)
            offset_y = rng.uniform(-15, 15)
            wx = max(10, min(CANVAS_W - 10, m["x"] + offset_x))
            wy = max(10, min(CANVAS_H - 10, m["y"] + offset_y))
            # Calculate distance to machine
            dist = math.sqrt((wx - m["x"]) ** 2 + (wy - m["y"]) ** 2)
            # Scale to metres (50px ≈ 10m)
            dist_m = dist * (10 / 50)
            workers.append({
                "worker_id": f"WN{j+1:03d}",
                "label": f"Worker N{j+1}",
                "x": round(wx, 1),
                "y": round(wy, 1),
                "zone": "NEAR_MACHINE",
                "proximity_status": "WARNING" if dist_m <= 10 else "SAFE",
                "nearest_machine": m["machine_code"],
                "distance_m": round(dist_m, 1),
            })

    return workers


@router.get("")
async def get_sitemap(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["engineer", "supervisor", "admin", "safety_officer"])),
):
    # Time seed: changes every 5 seconds for slow drift
    now = datetime.now(timezone.utc)
    time_seed = int(now.timestamp() // 5)

    machines_result = await db.execute(select(Machine).where(Machine.is_active == True))
    machines = machines_result.scalars().all()

    operators_result = await db.execute(select(Operator).where(Operator.is_active == True))
    operators = operators_result.scalars().all()
    op_map = {op.operator_id: op for op in operators}

    machine_positions = []
    for idx, m in enumerate(machines):
        x, y = _machine_pos(idx, m.status, time_seed)
        machine_positions.append({
            "machine_id": m.machine_id,
            "machine_code": m.machine_code,
            "machine_type": m.model.machine_type if m.model else "UNKNOWN",
            "status": m.status,
            "x": round(x, 1),
            "y": round(y, 1),
            "current_operator_id": m.current_operator_id,
            "current_operator_name": op_map[m.current_operator_id].name if m.current_operator_id and m.current_operator_id in op_map else None,
            "health_score": m.last_health_score,
            "speed_kmh": m.last_speed_kmh or 0,
            "proximity_warning_radius_px": 50,   # 10m
            "proximity_critical_radius_px": 25,  # 5m
        })

    workers = _generate_workers(machine_positions, time_seed)

    # Check any critical proximities
    proximity_alerts = []
    for w in workers:
        if w.get("proximity_status") in ("WARNING", "CRITICAL"):
            proximity_alerts.append({
                "worker_id": w["worker_id"],
                "nearest_machine": w.get("nearest_machine"),
                "distance_m": w.get("distance_m"),
                "status": w["proximity_status"],
            })

    payload = {
        "zones": ZONES,
        "machines": machine_positions,
        "workers": workers,
        "proximity_alerts": proximity_alerts,
        "canvas": {"width": CANVAS_W, "height": CANVAS_H},
        "as_of": now.isoformat(),
    }
    return ApiResponse(data=payload)


@router.post("/simulate-approach")
async def simulate_worker_approach(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(["engineer", "supervisor", "admin", "safety_officer"])),
):
    """
    Move a simulated worker directly toward the nearest active machine.
    Fires PROXIMITY_HAZARD scenario and broadcasts SITE_MAP_UPDATE.
    """
    now = datetime.now(timezone.utc)

    # Find first active machine
    mach_result = await db.execute(
        select(Machine).where(Machine.is_active == True, Machine.status == "ACTIVE").limit(1)
    )
    target_machine = mach_result.scalar_one_or_none()

    if not target_machine:
        return ApiResponse(data={"status": "no_active_machine", "message": "No active machine to approach."})

    # Position worker at 3.8m distance (critical proximity)
    mx, my = _machine_pos(0, "ACTIVE", int(now.timestamp() // 5))
    wx = mx + 19  # ~19px ≈ 3.8m (50px = 10m)
    wy = my + 0

    worker_data = {
        "worker_id": "W_SIMULATED",
        "label": "Simulated Worker",
        "x": round(wx, 1),
        "y": round(wy, 1),
        "zone": "NEAR_MACHINE",
        "proximity_status": "CRITICAL",
        "nearest_machine": target_machine.machine_code,
        "distance_m": 3.8,
    }

    # Broadcast the site map update with the approaching worker
    await ws_manager.broadcast({
        "type": "SITE_MAP_UPDATE",
        "payload": {
            "event": "WORKER_APPROACH",
            "worker": worker_data,
            "machine_id": target_machine.machine_id,
            "machine_code": target_machine.machine_code,
            "distance_m": 3.8,
            "alert_level": "CRITICAL",
            "timestamp": now.isoformat(),
        },
    })

    # Also trigger the proximity hazard scenario via simulator service
    try:
        from ..services.simulator_service import SimulatorService
        sim = SimulatorService(db)
        result = await sim.activate(
            "PROXIMITY_HAZARD",
            machine_id=target_machine.machine_id,
            operator_id=target_machine.current_operator_id,
        )
        await db.commit()
        logger.info(f"Proximity scenario activated: {result}")
    except Exception as e:
        logger.warning(f"Could not activate proximity scenario: {e}")

    return ApiResponse(data={
        "status": "simulated",
        "worker": worker_data,
        "machine_code": target_machine.machine_code,
        "broadcast": "SITE_MAP_UPDATE + PROXIMITY_HAZARD scenario activated",
    })
