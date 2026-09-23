# Spec 6 — ML Models & Analytics

## Status: READY FOR IMPLEMENTATION

---

## Requirements

### REQ-6.1 Task ETA prediction model
- **Model**: RandomForestRegressor
- **Target**: `actual_task_duration_minutes`
- **Features**:
  - task_type (encoded), machine_type (encoded), machine_age_years
  - operator_skill_level (1-5), operator_experience_years
  - target_quantity, material_type (encoded)
  - weather_condition (encoded), temperature_celsius, rainfall_mm, wind_speed_kmh
  - terrain_type (encoded), machine_load_percent
  - historical_avg_duration_minutes (same task_type + operator)
  - machine_utilization_percent
- **Output**: `{ predicted_minutes: float, confidence_interval: [float, float], features_used: dict }`
- Train script: `ml/training/train_eta.py`
- Inference: `ml/inference/predict_eta.py`
- Model saved: `ml/models/eta_model.joblib`
- Exposed via: `POST /ml/predict-eta`

### REQ-6.2 Operator anomaly detection
- **Model**: IsolationForest
- **Features** (rolling window per operator, last 30 minutes):
  - avg_speed, max_speed, sudden_acceleration_count, sudden_braking_count
  - idle_duration_minutes, fuel_consumption_rate, engine_rpm
  - machine_load_percent, cycle_time_minutes, proximity_event_count
- **Output**: `{ score: float, label: "NORMAL"|"UNUSUAL", reason: str, contributing_features: dict }`
- Reason must be human-readable: "Idle duration (42 min) is significantly above this operator's normal range (8 min avg)"
- Train script: `ml/training/train_anomaly.py`
- Inference: `ml/inference/predict_anomaly.py`
- Model: `ml/models/anomaly_model.joblib`
- Exposed via: `POST /ml/anomaly-check`

### REQ-6.3 Machine health score
- **Not ML** — deterministic weighted formula, computed in `backend/app/services/machine_health.py`
- Components and weights:
  ```
  engine_health     (0.30): RPM normal range, temp OK, oil pressure OK, no fault codes
  fuel_health       (0.15): fuel level, consumption rate vs baseline
  hydraulic_health  (0.20): pressure in range, temperature OK
  electrical_health (0.10): battery voltage in range
  mechanical_health (0.15): vibration level, brake status, track condition
  maintenance_score (0.10): days since last service, upcoming service due
  ```
- Output: `{ overall: float (0-100), components: { engine: float, fuel: float, ... }, alerts: list }`
- Exposed via: `GET /machines/:id/health`

### REQ-6.4 Productivity analytics
- Computed from tasks + telemetry aggregates
- `GET /analytics/productivity` — site/date range filterable
- Returns: tasks_completed, completion_rate, material_moved, cycles_per_hour,
  avg_cycle_time, machine_utilization_pct, operator_utilization_pct,
  idle_time_pct, fuel_efficiency (work/fuel), avg_eta_accuracy_pct

### REQ-6.5 ML API endpoints
```
POST /ml/predict-eta          body: TaskFeatures → ETAPrediction
POST /ml/anomaly-check        body: OperatorWindowFeatures → AnomalyResult
GET  /ml/model-status         → { eta_model: loaded/missing, anomaly_model: loaded/missing }
POST /ml/retrain              admin only → triggers background retraining
```

### REQ-6.6 Training recommendation engine
- Rule-based (not ML) for MVP
- Rules:
  - proximity_events > 3 in last 7 days → recommend "Proximity Safety Awareness" module
  - excessive_idle > 5 occurrences → recommend "Fuel Efficient Operation" module
  - speed_violations > 2 → recommend "Safe Operating Speeds" module
  - cert expiring in 30 days → recommend "Certification Renewal" module
  - anomaly_detected = UNUSUAL → recommend "Advanced Machine Operation" module
- Exposed via: `GET /operators/:id/training-recommendations`

---

## Design

### Training pipeline
```
data/generated/telemetry.parquet  (or demo_seed.sql)
  ↓
ml/training/train_eta.py
  → load data
  → feature engineering
  → train/test split (80/20)
  → fit RandomForestRegressor(n_estimators=100, random_state=42)
  → evaluate (MAE, RMSE, R²)
  → save to ml/models/eta_model.joblib
  → print metrics

ml/training/train_anomaly.py
  → load operator telemetry windows
  → fit IsolationForest(contamination=0.05, random_state=42)
  → save to ml/models/anomaly_model.joblib
```

### Inference integration
```
backend/app/services/ml_service.py
  → loads models on startup (or lazy loads)
  → exposes predict_eta(features) and check_anomaly(features)
  → returns structured dicts matching output specs above
  → if model not found: returns mock predictions with disclaimer
```

### Mock mode
If model `.joblib` files not present, `ml_service.py` returns:
```json
{
  "predicted_minutes": 65,
  "confidence_interval": [55, 75],
  "mock": true,
  "message": "Model not trained — showing demo prediction"
}
```
This ensures the demo works even before training runs.

---

## Tasks

- [ ] Create ml/training/train_eta.py
- [ ] Create ml/training/train_anomaly.py
- [ ] Create ml/inference/predict_eta.py
- [ ] Create ml/inference/predict_anomaly.py
- [ ] Create backend/app/services/ml_service.py (with mock fallback)
- [ ] Create backend/app/services/machine_health.py
- [ ] Create backend/app/services/scoring.py (productivity)
- [ ] Create backend/app/services/recommendations.py
- [ ] Create backend/app/routers/ml.py
- [ ] Create backend/app/routers/analytics.py
- [ ] Create frontend analytics page (/analytics)
- [ ] Create machine health drilldown component
- [ ] Create ETA prediction display component
- [ ] Create anomaly status badge component
- [ ] Create training recommendations component
- [ ] Run training on demo dataset, commit model files (small enough)
