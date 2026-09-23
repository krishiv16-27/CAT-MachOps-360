"""
Central configuration — all settings loaded from environment variables.
All safety thresholds live here so they can be tuned without code changes.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os


class Settings(BaseSettings):
    # ── App ────────────────────────────────────────────────────────────
    app_env: str = "development"
    app_version: str = "1.0.0"
    frontend_origin: str = "http://localhost:5173"

    # ── Database ───────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://cat:cat_secret@localhost:5432/machops360"
    use_sqlite: bool = False
    sqlite_url: str = "sqlite+aiosqlite:///./machops360_demo.db"

    # ── Redis ──────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Auth ───────────────────────────────────────────────────────────
    jwt_secret_key: str = "INSECURE_DEFAULT_CHANGE_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ── ML ─────────────────────────────────────────────────────────────
    ml_models_dir: str = "../ml/models"
    eta_model_path: str = "../ml/models/eta_model.joblib"
    anomaly_model_path: str = "../ml/models/anomaly_model.joblib"

    # ── RAG / LLM ──────────────────────────────────────────────────────
    llm_provider: str = "mock"  # mock | openai | local
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    local_llm_url: str = "http://localhost:11434"

    # ── Safety Thresholds ──────────────────────────────────────────────
    proximity_warning_meters: float = 10.0
    proximity_critical_meters: float = 5.0
    speed_limit_default_kmh: float = 20.0
    max_load_warning_pct: float = 90.0
    max_load_critical_pct: float = 100.0
    engine_temp_warning_c: float = 105.0
    engine_temp_critical_c: float = 115.0
    max_idle_minutes: float = 15.0
    max_continuous_operating_minutes: float = 90.0
    fatigue_risk_threshold: float = 0.75

    # ── Safety Score Weights (must sum to 1.0) ─────────────────────────
    safety_weight_seatbelt: float = 0.25
    safety_weight_proximity: float = 0.20
    safety_weight_speed: float = 0.15
    safety_weight_incident: float = 0.20
    safety_weight_prestart: float = 0.10
    safety_weight_training: float = 0.10

    # ── Machine Health Weights (must sum to 1.0) ───────────────────────
    health_weight_engine: float = 0.30
    health_weight_fuel: float = 0.15
    health_weight_hydraulics: float = 0.20
    health_weight_electrical: float = 0.10
    health_weight_mechanical: float = 0.15
    health_weight_maintenance: float = 0.10

    # ── Demo ───────────────────────────────────────────────────────────
    demo_seed: int = 42
    auto_seed_on_startup: bool = True

    @property
    def effective_database_url(self) -> str:
        return self.sqlite_url if self.use_sqlite else self.database_url

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Module-level convenience
settings = get_settings()
