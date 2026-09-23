# Design — CAT MachOps 360

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
│                                                                     │
│  ┌─────────────────┐    ┌─────────────────┐    ┌────────────────┐  │
│  │  Engineer /     │    │  Operator        │    │  Watch         │  │
│  │  Supervisor     │    │  Dashboard       │    │  Simulator     │  │
│  │  Dashboard      │    │                  │    │  (14 screens)  │  │
│  └────────┬────────┘    └────────┬─────────┘    └───────┬────────┘  │
│           │                      │                       │           │
│           └──────────────────────┴───────────────────────┘           │
│                         React 18 + TypeScript + Vite                │
│                         Zustand + React Query + Recharts             │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP + WebSocket
                             │ (Vite proxy: /api → :8000, /ws → :8000)
┌────────────────────────────▼────────────────────────────────────────┐
│                          API LAYER                                   │
│                                                                     │
│                    FastAPI (Python 3.11)                             │
│                    Pydantic v2 validation                            │
│                    JWT + RBAC middleware                             │
│                                                                     │
│  /auth  /operators  /machines  /tasks  /alerts  /incidents          │
│  /prestart  /analytics  /ml  /simulator  /cv  /training  /copilot   │
│                                                                     │
└──────┬──────────────────────┬──────────────────────┬───────────────┘
       │                      │                      │
┌──────▼──────┐    ┌──────────▼────────┐    ┌────────▼────────┐
│  SERVICES   │    │   INTELLIGENCE    │    │  REAL-TIME      │
│             │    │   ENGINE          │    │  LAYER          │
│ - Auth      │    │                   │    │                 │
│ - Operators │    │ Safety Engine     │    │ WebSocket       │
│ - Machines  │    │ (14 rules)        │    │ Manager         │
│ - Tasks     │    │                   │    │                 │
│ - Incidents │    │ Machine Health    │    │ Event Bus       │
│ - Training  │    │ (weighted score)  │    │ (in-memory)     │
│ - Simulator │    │                   │    │                 │
│             │    │ ML Service        │    │ Alert Broadcast │
│             │    │ (ETA + Anomaly)   │    │                 │
│             │    │                   │    │ Watch Push      │
│             │    │ Recommendations   │    │                 │
└──────┬──────┘    └──────────┬────────┘    └─────────────────┘
       │                      │
┌──────▼──────────────────────▼────────────────────────────────────────┐
│                          DATA LAYER                                  │
│                                                                     │
│  SQLite (demo)  /  PostgreSQL (production)                          │
│  SQLAlchemy 2.0 async + aiosqlite                                   │
│                                                                     │
│  24 tables: users, sites, zones, operators, machines,               │
│  tasks, telemetry, alerts, incidents, wearable_events,              │
│  dashcam_events, training_modules, operator_training, ...           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. SQLite for demo, PostgreSQL for production

**Decision:** Backend defaults to SQLite (`USE_SQLITE=true`) with automatic demo data seeding.

**Why:** Eliminates the PostgreSQL install requirement for the hackathon demo. The same SQLAlchemy models work with both databases — switching is a single env var change.

**Trade-off:** SQLite doesn't support concurrent writes at scale. PostgreSQL is required for production with multiple users.

### 2. Demo data auto-seeded on startup

**Decision:** `seed.py` runs on every backend startup when the database is empty.

**Why:** Zero-friction demo setup. Any team member can start the backend and immediately have realistic data. Data is deterministic (seed=42) — same data every time.

### 3. Rule-based safety engine (not ML)

**Decision:** Safety rules are deterministic Python functions, not ML models.

**Why:** Deterministic rules are debuggable, auditable, and always work. For a safety-critical domain, explainable rules are more appropriate than black-box ML. ML is used only for prediction (ETA) and pattern detection (anomaly), not for safety decisions.

### 4. Mock ML with real interfaces

**Decision:** ML models run in mock mode if `.joblib` files don't exist, returning realistic-looking predictions with a `mock: true` flag.

**Why:** The demo works without waiting for model training. Interfaces are identical between mock and real mode — when training scripts are run, the backend auto-loads the trained models.

### 5. In-process WebSocket (no Redis required for demo)

**Decision:** WebSocket broadcasts use an in-memory connection pool, not Redis pub/sub.

**Why:** Redis is not required for a single-process demo server. The architecture is designed to swap in Redis pub/sub for multi-worker production deployment — the ws_manager interface stays the same.

### 6. Simulated CV adapter

**Decision:** Computer vision uses a pluggable adapter pattern. The default is a simulation.

**Why:** Eliminates GPU/CUDA dependency. The adapter interface is identical to what a real OpenCV or YOLO integration would implement — the safety engine doesn't know whether events come from a real camera or a simulator.

---

## Data Flow

### Alert flow (end-to-end)

```
Telemetry event / CV event / Simulator scenario
           ↓
   SafetyEngine.evaluate()
   (14 deterministic rules)
           ↓
   Alert created → INSERT into alerts table
           ↓
   If CRITICAL → Incident created automatically
           ↓
   ws_manager.broadcast_alert()
           ↓
   ┌────────────────────────────────┐
   │ All connected WebSocket clients│
   │                                │
   │  Engineer dashboard → alert    │
   │  feed updates, KPI card        │
   │  increments                    │
   │                                │
   │  Operator watch → navigates    │
   │  to Active Alert screen,       │
   │  triggers haptic vibration     │
   └────────────────────────────────┘
```

### Pre-start authorization flow

```
Operator selects machine
         ↓
GET /prestart/checklist?machine_id=&operator_id=
         ↓
Backend auto-checks:
  - certification expiry (from operators table)
  - fuel level (from machine.last_fuel_level_pct)
  - active critical faults (from machine_faults table)
  - machine health score (from machine.last_health_score)
         ↓
Returns pre-populated checklist items
         ↓
Operator confirms remaining items in UI
         ↓
POST /prestart/submit
         ↓
Backend evaluates all required items
         ↓
Returns: AUTHORIZED / BLOCKED / REVIEW
         ↓
Updates machine_permissions table
Updates machine.authorization_status
```

### ML prediction flow

```
Task context (type, weather, terrain, operator skill, etc.)
         ↓
POST /ml/predict-eta
         ↓
ml_service.predict_eta()
         ↓
┌─────────────────────┐    ┌──────────────────────────┐
│ Model loaded?        │    │ No model found            │
│ → RandomForest       │    │ → Mock prediction         │
│   .predict()         │    │   (formula-based,         │
│ → real prediction    │    │    mock: true flag)       │
└─────────────────────┘    └──────────────────────────┘
         ↓
Returns: { predicted_minutes, confidence_interval, mock }
         ↓
Task.predicted_duration_minutes updated
Watch shows ETA
```

---

## Database Schema (key tables)

### Core entities

```
users
  user_id PK, email, name, hashed_password, role, operator_id FK

operators
  operator_id PK, employee_code, name, site_id, experience_years,
  skill_level, certification, certification_expiry, shift_status,
  continuous_operating_minutes, current_machine_id, safety_score

machines
  machine_id PK, machine_code, model_id FK, site_id, status,
  engine_hours, last_engine_temp_c, last_fuel_level_pct,
  last_health_score, current_operator_id, authorization_status

tasks
  task_id PK, site_id, machine_id, operator_id, task_type,
  target_quantity, completed_quantity, status,
  estimated_duration_minutes, predicted_duration_minutes,
  weather_condition, terrain_type

telemetry
  telemetry_id PK, timestamp, machine_id, operator_id,
  engine_rpm, engine_temperature_c, fuel_level_pct,
  hydraulic_pressure_bar, machine_speed_kmh, machine_load_pct,
  idle_time_min, seatbelt_status

alerts
  alert_id PK, timestamp, machine_id, operator_id,
  alert_type, severity, message, recommended_action,
  acknowledged, acknowledged_by, resolved

incidents
  incident_id PK, timestamp, machine_id, operator_id, alert_id FK,
  category, severity, description, status, is_auto_created

prestart_checks
  check_id PK, machine_id, operator_id, performed_at,
  items (JSON), authorization_status, blocked_reasons

wearable_events
  event_id PK, timestamp, operator_id,
  heart_rate, activity_level, fatigue_risk_indicator,
  attention_risk_indicator   ← labelled as risk indicators only

dashcam_events
  event_id PK, timestamp, camera_id, machine_id,
  person_detected, estimated_distance_m, confidence,
  event_type, alert_id FK
```

---

## Frontend Architecture

### State management

```
┌─────────────────────────────────────────────────────┐
│                   Zustand Stores                     │
│                                                     │
│  authStore     → user, token, role                  │
│  alertStore    → live alert list, unread count      │
│  watchStore    → current screen, active alert       │
│  kpiStore      → cached site overview KPIs          │
└──────────────────────┬──────────────────────────────┘
                       │ subscribed by components
┌──────────────────────▼──────────────────────────────┐
│              useWebSocket hook                       │
│                                                     │
│  Connects to ws://localhost:8000/ws?token=<jwt>      │
│  Handles: ALERT → alertStore + watchStore            │
│           KPI_UPDATE → kpiStore                      │
│           ALERT_ACKNOWLEDGED → alertStore            │
│  Reconnects automatically on disconnect              │
└──────────────────────┬──────────────────────────────┘
                       │ React Query for server state
┌──────────────────────▼──────────────────────────────┐
│              React Query                             │
│                                                     │
│  queryKey: ['machines'] → refetchInterval: 15s      │
│  queryKey: ['site-overview'] → refetchInterval: 30s  │
│  queryKey: ['alerts'] → refetchInterval: 10s        │
└─────────────────────────────────────────────────────┘
```

### Page routing

```
/login              → LoginPage (public)
/dashboard          → DashboardPage (engineer, supervisor, admin)
/machines           → MachinesPage
/machines/:id       → MachineDetailPage
/operators          → OperatorsPage
/operators/:id      → OperatorDetailPage (Operator 360)
/tasks              → TasksPage
/alerts             → AlertsPage
/incidents          → IncidentsPage
/prestart           → PrestartPage
/dashcam            → DashcamPage
/training           → TrainingPage
/analytics          → AnalyticsPage
/copilot            → CopilotPage (engineer, admin only)
/settings           → SettingsPage (engineer, admin, supervisor)
/operator           → OperatorDashboardPage (operator role)
/watch              → WatchPage
```

---

## API Structure

All endpoints under `/api/v1/`. Full contract in `docs/api-contracts.md`.

```
POST /auth/login
GET  /auth/me

GET  /analytics/site-overview       ← 7 KPI card values
GET  /analytics/productivity

GET  /machines                      ← fleet list
GET  /machines/:id                  ← machine detail
GET  /machines/:id/health           ← health drilldown
GET  /machines/:id/telemetry        ← time-series data

GET  /operators                     ← operator list
GET  /operators/:id                 ← operator detail
GET  /operators/:id/safety-score    ← 6-component score
GET  /operators/:id/timeline        ← daily task timeline
GET  /operators/:id/training-recommendations

GET  /tasks                         ← task list
POST /tasks/:id/start
POST /tasks/:id/complete

GET  /alerts                        ← alert list (filterable)
POST /alerts/:id/acknowledge

GET  /incidents
POST /incidents

GET  /prestart/checklist            ← auto-populated items
POST /prestart/submit               ← returns AUTHORIZED/BLOCKED/REVIEW

POST /ml/predict-eta                ← ETA prediction
POST /ml/anomaly-check              ← anomaly detection

POST /simulator/activate            ← trigger demo scenario
POST /simulator/reset

POST /cv/simulate                   ← inject CV event

POST /copilot/query                 ← RAG answer

WebSocket: ws://localhost:8000/ws?token=<jwt>
```

---

## ML Architecture

### ETA Model (Task Duration Prediction)

- **Algorithm:** RandomForestRegressor (n_estimators=100, random_state=42)
- **Target:** actual_task_duration_minutes
- **Features:** task_type, machine_type, machine_age, operator_skill, operator_experience, target_quantity, weather, temperature, rainfall, wind, terrain, machine_load, historical_avg_duration
- **Training:** `ml/training/train_eta.py`
- **Fallback:** formula-based mock with `mock: true` flag
- **Output:** `{ predicted_minutes, confidence_interval: [low, high] }`

### Anomaly Detection

- **Algorithm:** IsolationForest (contamination=0.05, random_state=42)
- **Features:** avg_speed, max_speed, sudden_acceleration_count, idle_duration, fuel_consumption_rate, engine_rpm, machine_load, cycle_time
- **Window:** last 30 telemetry rows for the operator
- **Output:** `{ score, label: NORMAL|UNUSUAL, reason }`
- **Language:** Neutral — "unusual pattern detected", not "unsafe behaviour"

### Machine Health Score

- **Type:** Deterministic weighted formula (no ML)
- **Components:** engine (30%), hydraulics (20%), fuel (15%), mechanical (15%), electrical (10%), maintenance (10%)
- **Why not ML:** Rule-based scoring is more auditable and explainable for safety-critical contexts

---

## Security Design

| Concern | Solution |
|---------|---------|
| Password storage | bcrypt hashing (passlib) |
| Authentication | JWT Bearer tokens, 60-minute expiry |
| Authorization | RBAC enforced at FastAPI Depends() level |
| Secrets | All in .env files, never committed |
| Audit trail | audit_logs table, write-only |
| Biometric privacy | Labelled as operational indicators, not medical data |
| QR codes | Operator ID only, no sensitive data |
| CORS | Restricted to frontend origin |
| SQL injection | Prevented by SQLAlchemy parameterized queries |

---

## Scalability Path

The demo runs on SQLite with a single FastAPI process. The architecture scales to production by:

1. Switch `USE_SQLITE=false`, set `DATABASE_URL` to PostgreSQL
2. Add Redis for WebSocket pub/sub (multi-worker broadcast)
3. Add Alembic migrations for schema evolution
4. Run multiple uvicorn workers behind nginx
5. Store large telemetry in Parquet/DuckDB, keep application data in PostgreSQL
6. Replace mock ML with trained models served via the same interface

No code changes required for steps 1–2. The interfaces are already designed for it.
