"""
CAT MachOps 360 — FastAPI Application
Main entry point. Registers all routers, middleware, and startup logic.
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .core.database import init_db
from .core.ws_manager import ws_manager

# Import all models so they're registered with Base
from .models import *  # noqa: F401, F403

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("Starting CAT MachOps 360 backend...")

    # Initialize database (create tables if not exists)
    await init_db()
    logger.info("Database initialized.")

    # Seed demo data if configured
    if settings.auto_seed_on_startup:
        try:
            from .core.seed import seed_demo_data
            await seed_demo_data()
        except Exception as e:
            logger.warning(f"Demo seed skipped: {e}")

    # Load ML models
    try:
        from .services.ml_service import ml_service
        ml_service.load_models()
        logger.info("ML models loaded.")
    except Exception as e:
        logger.warning(f"ML models not loaded: {e}")

    # Generate CSV datasets if not present
    try:
        from pathlib import Path
        csv_dir = Path(__file__).parent.parent.parent / "data" / "generated"
        csv_dir.mkdir(parents=True, exist_ok=True)
        if not (csv_dir / "operators_profile.csv").exists():
            import importlib.util
            gen_path = csv_dir.parent / "generators" / "csv_generator.py"
            spec = importlib.util.spec_from_file_location("csv_generator", gen_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            mod.write_csvs(csv_dir, seed=42)
            logger.info("CSV datasets generated.")
    except Exception as e:
        logger.warning(f"CSV generation skipped: {e}")

    logger.info(f"Server ready. ENV={settings.app_env} DB={'SQLite' if settings.use_sqlite else 'PostgreSQL'}")
    yield

    logger.info("Shutting down...")


app = FastAPI(
    title="CAT MachOps 360",
    description="CAT Smart Operator Intelligence Platform API",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from .routers import auth, operators, machines, tasks, alerts, incidents
from .routers import prestart, analytics, ml as ml_router, simulator, cv, training

app.include_router(auth.router,       prefix="/api/v1/auth",       tags=["auth"])
app.include_router(operators.router,  prefix="/api/v1/operators",  tags=["operators"])
app.include_router(machines.router,   prefix="/api/v1/machines",   tags=["machines"])
app.include_router(tasks.router,      prefix="/api/v1/tasks",      tags=["tasks"])
app.include_router(alerts.router,     prefix="/api/v1/alerts",     tags=["alerts"])
app.include_router(incidents.router,  prefix="/api/v1/incidents",  tags=["incidents"])
app.include_router(prestart.router,   prefix="/api/v1/prestart",   tags=["prestart"])
app.include_router(analytics.router,  prefix="/api/v1/analytics",  tags=["analytics"])
app.include_router(ml_router.router,  prefix="/api/v1/ml",         tags=["ml"])
app.include_router(simulator.router,  prefix="/api/v1/simulator",  tags=["simulator"])
app.include_router(cv.router,         prefix="/api/v1/cv",         tags=["cv"])
app.include_router(training.router,   prefix="/api/v1/training",   tags=["training"])

# RAG copilot (P1 — include if available)
try:
    from .routers import copilot
    app.include_router(copilot.router, prefix="/api/v1/copilot", tags=["copilot"])
except ImportError:
    logger.info("Copilot router not available yet.")

# Phase A/B/C new routers
from .routers import data_explorer, sitemap, compatibility
app.include_router(data_explorer.router, prefix="/api/v1/data-explorer", tags=["data-explorer"])
app.include_router(sitemap.router,       prefix="/api/v1/sitemap",       tags=["sitemap"])
app.include_router(compatibility.router, prefix="/api/v1/compatibility", tags=["compatibility"])


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    from .services.ml_service import ml_service
    return {
        "status": "ok",
        "version": settings.app_version,
        "database": "sqlite" if settings.use_sqlite else "postgresql",
        "ml_models": {
            "eta": "loaded" if ml_service.eta_model else "mock",
            "anomaly": "loaded" if ml_service.anomaly_model else "mock",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None):
    """
    Real-time event stream.
    Query param: ?token=<jwt>
    """
    # Basic token validation (full auth for demo — accept any valid-looking token)
    client_id = await ws_manager.connect(websocket, token)
    logger.info(f"WebSocket connected: {client_id}")
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_client_message(client_id, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        ws_manager.disconnect(client_id)


# ── Exception handlers ────────────────────────────────────────────────────────
@app.exception_handler(404)
async def not_found(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "NOT_FOUND", "message": "Resource not found"}},
    )


@app.exception_handler(500)
async def server_error(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "SERVER_ERROR", "message": "Internal server error"}},
    )
