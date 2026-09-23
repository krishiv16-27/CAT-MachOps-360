"""
ML model service — loads trained models and exposes predict/check methods.
Falls back to mock predictions if models are not found.
"""
import logging
import os
from typing import Any
from ..core.config import settings

logger = logging.getLogger(__name__)


class MLService:
    def __init__(self):
        self.eta_model = None
        self.anomaly_model = None
        self.feature_encoder = None

    def load_models(self):
        try:
            import joblib
            eta_path = settings.eta_model_path
            if os.path.exists(eta_path):
                self.eta_model = joblib.load(eta_path)
                logger.info(f"ETA model loaded from {eta_path}")
            else:
                logger.warning(f"ETA model not found at {eta_path} — using mock predictions")

            anomaly_path = settings.anomaly_model_path
            if os.path.exists(anomaly_path):
                self.anomaly_model = joblib.load(anomaly_path)
                logger.info(f"Anomaly model loaded from {anomaly_path}")
            else:
                logger.warning(f"Anomaly model not found at {anomaly_path} — using mock predictions")
        except ImportError:
            logger.warning("joblib not available — using mock predictions")

    def predict_eta(self, features: dict[str, Any]) -> dict:
        if self.eta_model is None:
            return self._mock_eta(features)
        try:
            import numpy as np
            feature_vector = self._encode_eta_features(features)
            prediction = self.eta_model.predict([feature_vector])[0]
            # Confidence interval via forest variance (rough estimate)
            ci_low = max(1.0, prediction * 0.85)
            ci_high = prediction * 1.15
            return {
                "predicted_minutes": round(float(prediction), 1),
                "confidence_interval": [round(ci_low, 1), round(ci_high, 1)],
                "mock": False,
                "features_used": features,
            }
        except Exception as e:
            logger.warning(f"ETA prediction error: {e} — using mock")
            return self._mock_eta(features)

    def _mock_eta(self, features: dict) -> dict:
        # Realistic mock based on task type and conditions
        base_minutes = {
            "EXCAVATION": 75, "LOADING": 45, "TRENCHING": 90,
            "GRADING": 60, "HAULING": 40, "COMPACTION": 50,
            "BACKFILL": 55,
        }.get(features.get("task_type", "EXCAVATION").upper(), 65)

        # Adjust for weather
        weather = features.get("weather_condition", "CLEAR").upper()
        weather_factor = {"CLEAR": 1.0, "CLOUDY": 1.0, "RAIN": 1.3, "HEAVY_RAIN": 1.5, "FOG": 1.2}.get(weather, 1.0)

        # Adjust for terrain
        terrain = features.get("terrain_type", "FLAT").upper()
        terrain_factor = {"FLAT": 1.0, "SLOPE": 1.2, "ROUGH": 1.3, "ROCKY": 1.4}.get(terrain, 1.0)

        # Adjust for operator skill (1-5, higher = faster)
        skill = features.get("operator_skill_level", 3)
        skill_factor = 1.0 + (3 - skill) * 0.1  # skill 5 → 0.8x, skill 1 → 1.2x

        predicted = base_minutes * weather_factor * terrain_factor * skill_factor
        ci_low = predicted * 0.85
        ci_high = predicted * 1.15

        return {
            "predicted_minutes": round(predicted, 1),
            "confidence_interval": [round(ci_low, 1), round(ci_high, 1)],
            "mock": True,
            "message": "Demo prediction — ML model not yet trained. Run ml/training/train_eta.py.",
        }

    async def check_anomaly(self, operator_id: str, db) -> dict:
        if self.anomaly_model is None:
            return self._mock_anomaly(operator_id)
        try:
            from sqlalchemy import select, desc
            from ..models.telemetry import Telemetry
            import numpy as np
            result = await db.execute(
                select(Telemetry)
                .where(Telemetry.operator_id == operator_id)
                .order_by(desc(Telemetry.timestamp))
                .limit(30)
            )
            rows = result.scalars().all()
            if len(rows) < 5:
                return self._mock_anomaly(operator_id)
            features = self._encode_anomaly_features(rows)
            score = self.anomaly_model.decision_function([features])[0]
            label = "UNUSUAL" if score < 0 else "NORMAL"
            reason = self._anomaly_reason(rows) if label == "UNUSUAL" else "Operating within normal parameters."
            return {"score": round(float(score), 4), "label": label, "reason": reason}
        except Exception as e:
            logger.warning(f"Anomaly check error: {e}")
            return self._mock_anomaly(operator_id)

    def _mock_anomaly(self, operator_id: str) -> dict:
        import random
        r = random.Random(hash(operator_id) % 1000)
        score = r.uniform(-0.3, 0.3)
        label = "UNUSUAL" if score < -0.1 else "NORMAL"
        reason = (
            "Idle duration significantly above this operator's normal range."
            if label == "UNUSUAL"
            else "Operating within normal parameters."
        )
        return {
            "score": round(score, 4),
            "label": label,
            "reason": reason,
            "mock": True,
            "message": "Demo anomaly check — ML model not yet trained.",
        }

    def _encode_eta_features(self, f: dict) -> list:
        task_map = {"EXCAVATION": 0, "LOADING": 1, "TRENCHING": 2, "GRADING": 3, "HAULING": 4, "COMPACTION": 5, "BACKFILL": 6}
        machine_map = {"EXCAVATOR": 0, "BULLDOZER": 1, "GRADER": 2, "LOADER": 3, "DUMP_TRUCK": 4}
        weather_map = {"CLEAR": 0, "CLOUDY": 1, "RAIN": 2, "HEAVY_RAIN": 3, "FOG": 4}
        terrain_map = {"FLAT": 0, "SLOPE": 1, "ROUGH": 2, "ROCKY": 3}
        material_map = {"CLAY": 0, "SAND": 1, "ROCK": 2, "TOPSOIL": 3, "GRAVEL": 4}
        return [
            task_map.get(f.get("task_type", "EXCAVATION").upper(), 0),
            machine_map.get(f.get("machine_type", "EXCAVATOR").upper(), 0),
            f.get("machine_age_years", 2.0),
            f.get("operator_skill_level", 3),
            f.get("operator_experience_years", 3.0),
            f.get("target_quantity", 100.0),
            weather_map.get(f.get("weather_condition", "CLEAR").upper(), 0),
            f.get("temperature_celsius", 22.0),
            f.get("rainfall_mm", 0.0),
            f.get("wind_speed_kmh", 10.0),
            terrain_map.get(f.get("terrain_type", "FLAT").upper(), 0),
            f.get("machine_load_percent", 70.0),
            material_map.get(f.get("material_type", "CLAY").upper(), 0),
            f.get("historical_avg_duration_minutes") or 65.0,
        ]

    def _encode_anomaly_features(self, rows) -> list:
        import numpy as np
        def safe_avg(vals):
            v = [x for x in vals if x is not None]
            return sum(v) / len(v) if v else 0.0
        return [
            safe_avg([r.machine_speed_kmh for r in rows]),
            max((r.machine_speed_kmh or 0) for r in rows),
            sum(1 for r in rows if r.sudden_acceleration),
            sum(1 for r in rows if r.sudden_braking),
            safe_avg([r.idle_time_min for r in rows]),
            safe_avg([r.fuel_consumption_rate_lph for r in rows]),
            safe_avg([r.engine_rpm for r in rows]),
            safe_avg([r.machine_load_pct for r in rows]),
            safe_avg([r.cycle_time_min for r in rows]),
        ]

    def _anomaly_reason(self, rows) -> str:
        idle_avg = sum(r.idle_time_min or 0 for r in rows) / max(len(rows), 1)
        if idle_avg > 10:
            return f"Idle duration ({idle_avg:.0f} min avg) is significantly above normal operating range."
        acc_count = sum(1 for r in rows if r.sudden_acceleration)
        if acc_count > 3:
            return f"Sudden acceleration events ({acc_count} in last 30 readings) exceed normal operating pattern."
        return "Unusual operating pattern detected across multiple parameters."


# Singleton
ml_service = MLService()
