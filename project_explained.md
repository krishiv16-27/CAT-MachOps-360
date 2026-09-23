# CAT MachOps 360 — Project Explained
### Complete Technical Reference for Judges, Developers & Reviewers

> **Last updated:** Auto-generated at completion of hackathon build.
> Reflects code that has been written and verified running on localhost.

---

## 1. Project Overview

CAT MachOps 360 is an intelligent human-machine operations platform built for Caterpillar construction and mining sites. It integrates operator monitoring, machine telemetry, computer vision, machine learning, and real-time safety alerting into a single command center.

**Central concept:**
```
OPERATOR + MACHINE + ENVIRONMENT + TASK
                  ↓
         INTELLIGENCE ENGINE
                  ↓
SAFETY + PRODUCTIVITY + PREDICTION + RECOMMENDATION
```

The operator is treated as a **first-class entity**, not a machine accessory. The system monitors human factors (fatigue indicators, operating patterns, certifications) alongside machine health and environmental conditions.

---

## 2. Problem Statement

Caterpillar construction and mining sites face:

- **Safety incidents** from proximity hazards, seatbelt violations, operator fatigue, and machine overloading
- **Productivity loss** from unplanned downtime, excessive idling, poor task estimation, and equipment faults
- **Operational blindness** — supervisors lack real-time visibility into what every operator and machine is doing simultaneously
- **Reactive maintenance** — faults discovered after breakdowns rather than predicted in advance
- **Training gaps** — operators with safety deficiencies aren't identified until an incident occurs

Existing systems monitor machines or safety separately. None integrate the operator, machine, environment, and task into a unified intelligence layer.

---

## 3. Solution

CAT MachOps 360 provides:

1. **Real-time command center** — Engineers see all 10 machines, 10 operators, safety scores, alerts, and KPIs on one screen that updates live
2. **Safety engine** — 14 deterministic rules fire real-time alerts when thresholds are crossed; CRITICAL alerts auto-create incidents
3. **Operator 360** — Full daily timeline, safety score breakdown, anomaly detection, and personalised training recommendations per operator
4. **Smart Watch simulator** — 14-screen wearable UI receives alerts, shows task ETA, operator ID QR; haptic vibration on CRITICAL alerts
5. **Pre-start authorization** — Blocks machine operation if certification expired, fuel critical, or machine has active critical faults
6. **ML task ETA** — RandomForest predicts task duration factoring weather, terrain, skill, machine age (R²=0.865, MAE=12 min)
7. **Anomaly detection** — IsolationForest flags unusual operating patterns with human-readable explanations
8. **AI copilot** — RAG-style engineer chatbot answers from synthetic machine manuals and safety documentation
9. **Demo scenario system** — 12 one-click scenarios trigger the full alert pipeline for live demonstrations

---

## 4. Full Feature List

### P0 — Implemented and Working
- ✅ Engineer/Supervisor command center dashboard (7 clickable KPI cards)
- ✅ Machine fleet list with health, fuel, temperature, utilization
- ✅ Machine health drilldown: engine, fuel, hydraulics, electrical, mechanical, maintenance
- ✅ Operator list with safety scores, shift status, certification status
- ✅ Operator 360 profile: daily timeline, safety score components, anomaly, recommendations
- ✅ Task management: progress, ETA, weather/terrain context
- ✅ Safety engine: 14 rules, configurable thresholds, CRITICAL→incident auto-creation
- ✅ Real-time alert feed via WebSocket
- ✅ Alert acknowledgement (from dashboard and watch)
- ✅ Incident management with auto-creation and manual creation
- ✅ Pre-start machine check: 10 required + 1 optional items, AUTHORIZED/BLOCKED/REVIEW
- ✅ Watch simulator: 14 navigable screens, haptic vibration, QR code, alert push
- ✅ Operator dashboard (simplified role-specific view)
- ✅ RBAC: 6 roles enforced at API level
- ✅ JWT authentication
- ✅ Demo data auto-seeded on startup (10 operators, 10 machines, 20 tasks)
- ✅ 12 demo scenario controls (proximity hazard, overheating, seatbelt, etc.)
- ✅ Dashcam CV simulation: inject events, fire alerts
- ✅ Training hub: 15 modules, completion tracking
- ✅ Training recommendations: rule-based, triggered by alert history
- ✅ ML ETA prediction: RandomForest, R²=0.865, trained on synthetic data
- ✅ ML anomaly detection: IsolationForest, trained on synthetic operator windows
- ✅ Machine health score: weighted formula (6 components)
- ✅ Operator safety score: weighted formula (6 components)
- ✅ AI copilot: mock RAG with realistic answers
- ✅ Analytics page: productivity metrics, radar chart
- ✅ Dataset generator: demo/dev/stress profiles, Parquet + SQL output
- ✅ SQLite demo mode (no PostgreSQL required)

### P1 — Partially Implemented
- ⚠️ RAG copilot: mock mode only (real ChromaDB+LLM integration designed, not wired)
- ⚠️ ML models: trained on synthetic data (real telemetry training path documented)

### P2 — Architecture Designed, Not Implemented
- 📋 Real smartwatch/BLE integration
- 📋 Real CAT machine CAN bus telemetry
- 📋 Real IoT gateway
- 📋 Redis pub/sub for multi-worker WebSocket
- 📋 Docker compose production setup

---

## 5. Architecture

```
┌─────────────────────────────────────────────────────┐
│                  FRONTEND (React)                    │
│  :5173  Vite dev server                             │
│  17 pages · 6 Zustand stores · WebSocket hook       │
└────────────────────┬────────────────────────────────┘
                     │ HTTP /api/v1 + WebSocket /ws
                     │ (proxied by Vite to :8000)
┌────────────────────▼────────────────────────────────┐
│               BACKEND (FastAPI)                      │
│  :8000  uvicorn ASGI                               │
│  13 routers · 7 services · 24 DB tables             │
│                                                     │
│  Safety Engine → Alert → WebSocket broadcast        │
│  ML Service (ETA + Anomaly, real models loaded)     │
│  Simulator Service (12 scenarios)                   │
└──────────┬─────────────────────────────────────────┘
           │ SQLAlchemy async
┌──────────▼──────────────────────────────────────────┐
│              DATA LAYER                              │
│  SQLite (demo) · PostgreSQL (production)             │
│  24 tables, auto-seeded, 10k+ rows on first start   │
└─────────────────────────────────────────────────────┘

Separate processes (offline):
  ml/training/train_eta.py      → ml/models/eta_model.joblib
  ml/training/train_anomaly.py  → ml/models/anomaly_model.joblib
  data/generators/generate_data.py → data/seed/*.sql + data/generated/*.parquet
```

---

## 6. Tech Stack

| Layer | Technology | Version | Why chosen |
|-------|-----------|---------|-----------|
| Frontend | React + TypeScript | 18.x | Component model, type safety |
| Build | Vite | 5.x | Fast HMR, built-in proxy |
| Styling | Tailwind CSS | 3.x | Industrial dark UI, zero custom CSS |
| Charts | Recharts | 2.x | Lightweight, composable, no WebGL |
| State | Zustand | 4.x | Minimal boilerplate, no Redux complexity |
| Server state | React Query | 5.x | Caching, refetch intervals, loading states |
| QR | qrcode.react | 3.x | Operator ID QR generation |
| Backend | FastAPI | 0.111 | Async, auto-docs, Pydantic v2 |
| ORM | SQLAlchemy | 2.0 async | Works with SQLite and PostgreSQL |
| DB (demo) | SQLite/aiosqlite | — | Zero install, instant start |
| DB (prod) | PostgreSQL | 15 | Concurrent writes, JSONB, extensions |
| Auth | python-jose + passlib | — | JWT + bcrypt, industry standard |
| ML | scikit-learn | 1.8 | No GPU needed, interpretable |
| Dataset | pandas + pyarrow | — | Parquet support, fast generation |
| Fake data | Faker | 24.x | Realistic names, locations |

---

## 7. Database Schema

### 24 tables across 5 domains:

**Auth & Identity:** `users`

**Operations:** `sites`, `zones`, `operators`, `operator_certifications`, `operator_breaks`, `machines`, `machine_models`, `tasks`, `task_events`

**Telemetry:** `telemetry`, `wearable_events`, `environmental_data`

**Safety:** `alerts`, `proximity_events`, `incidents`, `prestart_checks`, `machine_permissions`, `dashcam_events`, `audit_logs`

**Maintenance & Training:** `machine_faults`, `machine_maintenance`, `training_modules`, `operator_training`, `training_recommendations`

### Key design decisions

- All PKs are UUID strings — no integer autoincrement sequences
- All timestamps are `TIMESTAMP WITH TIME ZONE` in UTC
- Soft deletes via `is_active` boolean — no hard deletes on operational data
- `trigger_data` and `items` fields use JSON columns for flexible event payloads
- `wearable_events` columns labelled as risk indicators — not medical data fields

---

## 8. Dataset Schema & Generation

### Generator entry point
```bash
python data/generators/generate_data.py --profile demo|dev|stress --seed 42
```

### Profiles
| Profile | Machines | Operators | Telemetry rows | Generation time |
|---------|----------|-----------|----------------|-----------------|
| demo | 10 | 10 | ~1,200 | ~2s |
| dev | 50 | 100 | ~144,000 | ~30s |
| stress | 200 | 500 | ~2,016,000 | ~5-10 min |

### Data realism rules (not random)
- Engine temperature **rises** with machine load (linear correlation)
- Fuel level **decreases** over time faster at higher load
- Engine RPM **correlates** with load (1000 + load×12)
- Hydraulic pressure **varies** with movement activity
- Task duration **multiplied** by weather factor (rain=1.25×) and terrain factor (rocky=1.40×)
- Operator skill level **reduces** task duration (skill 5 = 0.78× baseline)
- Machine age **slightly increases** maintenance risk probability
- Fatigue risk indicator **drifts upward** over a long shift
- 5% of operators have expired or near-expiry certifications (deliberate)
- ~5% of telemetry windows contain injected anomaly patterns

### Output
- `data/seed/<profile>_seed.sql` — SQL INSERTs for all application entities (committed for demo)
- `data/generated/<profile>_telemetry.parquet` — large time-series (gitignored)
- `data/generated/<profile>_wearable_events.parquet` — biometric events (gitignored)

---

## 9. ML Models

### 9.1 Task ETA Prediction

**File:** `ml/training/train_eta.py` → `ml/models/eta_model.joblib`

**Algorithm:** RandomForestRegressor (n_estimators=100, max_depth=12, random_state=42)

**Target variable:** `actual_duration_minutes`

**Features (14):**
| Feature | Encoding | Impact |
|---------|---------|--------|
| task_type | integer (0-6) | Base duration varies 40-90 min |
| machine_type | integer (0-5) | Minor effect |
| machine_age_years | float | +1% per year |
| operator_skill_level | integer 1-5 | Skill 5 = 22% faster than skill 1 |
| operator_experience_years | float | Correlated with skill |
| target_quantity | float | More quantity = longer |
| weather_condition | integer | HEAVY_RAIN = +50% duration |
| temperature_celsius | float | Minor effect |
| rainfall_mm | float | Correlated with weather |
| wind_speed_kmh | float | Minor effect |
| terrain_type | integer | ROCKY = +40% duration |
| machine_load_percent | float | Higher load = slightly slower |
| material_type | integer | Rock harder than clay |
| historical_avg_duration_minutes | float | **Top predictor (64% importance)** |

**Performance (trained on 5,000 synthetic samples):**
- MAE: 12.3 minutes
- RMSE: 16.1 minutes
- R²: 0.865

**Output:** `{ predicted_minutes: float, confidence_interval: [low, high], mock: false }`

**Confidence interval:** ±15% of prediction (rough estimate, not statistically rigorous for demo)

**Mock fallback:** If model not loaded, returns formula-based prediction with `mock: true`.

---

### 9.2 Operator Anomaly Detection

**File:** `ml/training/train_anomaly.py` → `ml/models/anomaly_model.joblib`

**Algorithm:** IsolationForest (n_estimators=100, contamination=0.05, random_state=42)

**Features (9) — aggregated over last 30 telemetry rows per operator:**
- avg_speed_kmh, max_speed_kmh
- sudden_acceleration_count, sudden_braking_count
- avg_idle_time_min
- avg_fuel_consumption_rate_lph
- avg_engine_rpm
- avg_machine_load_pct
- avg_cycle_time_min

**Training:** StandardScaler normalisation + IsolationForest on 10,000 synthetic windows (5% injected anomalies).

**Output:**
```json
{
  "score": -0.12,        // negative = anomalous
  "label": "UNUSUAL",
  "reason": "Idle duration (35 min) significantly above this operator's normal range.",
  "mock": false
}
```

**Language policy:** Output uses neutral language — "unusual pattern detected", never "unsafe behaviour" or "intoxicated".

**Disclaimer:** "Detects unusual operating patterns. NOT a diagnostic or safety certification tool."

---

### 9.3 Machine Health Score

**File:** `backend/app/services/machine_health.py`

**Type:** Deterministic weighted formula (no ML — deliberately, for auditability)

**Components and weights:**
| Component | Weight | Key inputs |
|-----------|--------|-----------|
| Engine | 30% | RPM, temperature, oil pressure, fault codes |
| Hydraulics | 20% | Pressure deviation from nominal, temperature |
| Fuel | 15% | Level %, consumption rate |
| Mechanical | 15% | Vibration (g), brake status |
| Electrical | 10% | Battery voltage |
| Maintenance | 10% | Days since last service, hours until next service |

**Why formula not ML:** Rule-based scoring is auditable and explainable. For safety-critical decisions, explainability > accuracy.

---

### 9.4 Operator Safety Score

**File:** `backend/app/services/scoring.py`

**Type:** Weighted composite — lookback 7 days

**Components:**
| Component | Weight | Measurement |
|-----------|--------|-------------|
| Seatbelt compliance | 25% | -15 per SEATBELT_UNFASTENED alert |
| Proximity events | 20% | -10 per proximity alert |
| Speed violations | 15% | -12 per SPEED_VIOLATION alert |
| Incident rate | 20% | -20 per incident |
| Pre-start compliance | 10% | % of checks that passed |
| Training completion | 10% | % of mandatory modules completed |

**Label:** Always shown as "Operational Safety Score (Demo Index)" — not presented as scientifically validated.

---

## 10. CV Architecture

**Pattern:** Pluggable adapter — CVAdapter abstract base class with two implementations.

```
CVAdapter (abstract)
  ├── SimulatedCVAdapter   ← Demo default (no camera needed)
  └── OpenCVAdapter        ← Stub for real camera integration
```

**Flow:**
```
CV event (simulated or real)
  → POST /cv/simulate  or  POST /cv/events
  → DashcamEvent saved to DB
  → safety_engine.evaluate_cv_event()
  → Alert created if person detected within threshold
  → WebSocket broadcast
  → Watch notified
```

**Demo features:**
- Person detected at distance → PROXIMITY_CRITICAL or PROXIMITY_WARNING alert
- Restricted zone entry → DASHCAM_PERSON_ZONE alert
- Attention events (eye closure, yawn) → labelled "demo simulation only"

---

## 11. RAG Copilot Architecture

**Status:** Mock mode implemented. Full pipeline designed.

**Mock mode** (current): Pre-written keyword-matched responses for common queries. Covers hydraulic warnings, maintenance, proximity incidents, training status. Returns `mock: true`.

**Full pipeline** (designed):
```
Synthetic documents (rag/documents/*.md)
  → parse + chunk (500-token chunks)
  → embed (sentence-transformers)
  → store (ChromaDB local)

Query
  → embed query
  → retrieve top-5 chunks
  → detect structured data queries (regex matching)
  → fetch live DB data if needed
  → build prompt: chunks + DB context
  → LLM (openai / local Ollama / mock)
  → return answer + source references
```

**Documents (synthetic, not real CAT content):**
- `excavator_manual.md`
- `safety_guidelines.md`
- `maintenance_schedule.md`
- `fault_codes.md`
- `operator_training_guide.md`
- `faq.md`

**Disclaimer shown on every response:** "Responses generated from synthetic demo documents — not validated CAT documentation."

---

## 12. Watch Architecture

**Page:** `/watch` — standalone page, works for both operator and engineer roles.

**14 screens:** home, current-task, task-progress, next-task, safety-status, active-alert, break-recommendation, machine-status, emergency, shift-summary, todays-tasks, safety-events, qr-code, training

**State:** Zustand `watchStore` — `currentScreen`, `activeAlert`, `isVibrating`

**Alert push flow:**
```
Backend fires alert
  → WebSocket ALERT message
  → useWebSocket hook receives
  → alertStore.addAlert()
  → if severity HIGH|CRITICAL: watchStore.setActiveAlert()
  → WatchPage re-renders to ActiveAlertScreen
  → navigator.vibrate([500, 100, 500]) called
  → Visual pulse animation plays
```

**QR code:** Contains `{ "operator_id": "<uuid>" }` only. No sensitive data.

**Haptic fallback:** Visual red pulsing border on watch frame when vibration API unsupported.

---

## 13. RBAC

**6 roles:** operator, supervisor, engineer, safety_officer, maintenance_engineer, admin

**Enforcement:** Server-side via FastAPI `Depends(require_role([...]))`. Frontend provides role-based navigation but server always re-validates.

**JWT payload:** `{ sub: user_id, role: role, name: name, operator_id: operator_id|null }`

**Token expiry:** 60 minutes (configurable via `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`)

---

## 14. Security

| Concern | Implementation |
|---------|---------------|
| Password storage | bcrypt (passlib, bcrypt==4.0.1) |
| Auth tokens | JWT HS256, 60-minute access tokens |
| RBAC | Enforced at FastAPI dependency level on every protected route |
| Secrets | All in `.env` files, `.env` in `.gitignore` |
| SQL injection | SQLAlchemy parameterized queries — no raw SQL |
| CORS | Restricted to `FRONTEND_ORIGIN` env var |
| Audit trail | `audit_logs` table — write-only, no delete endpoint |
| Biometric privacy | Labelled as operational risk indicators; no diagnostic claims |
| QR codes | Operator ID only — no biometric or personal data |

---

## 15. Privacy

- Wearable/biometric fields (`heart_rate`, `fatigue_risk_indicator`, `attention_risk_indicator`) are labelled operational risk indicators throughout the codebase, UI, and API responses
- The system never claims diagnostic accuracy for any health assessment
- `breathalyzer_status` field only present if explicitly configured as a simulated separate sensor
- QR codes contain `operator_id` only
- All data in this build is synthetic — no real personal data used

---

## 16. API Reference

Full API contract in `docs/api-contracts.md`. Summary:

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /auth/login | Public | Returns JWT |
| GET | /auth/me | Any | Current user |
| GET | /analytics/site-overview | Any | 7 KPI values |
| GET | /machines | Any | Fleet list |
| GET | /machines/:id/health | Any | Health drilldown |
| GET | /operators | Supervisor+ | Operator list |
| GET | /operators/:id/safety-score | Supervisor+ | 6-component score |
| GET | /operators/:id/timeline | Own/Supervisor+ | Daily timeline |
| GET | /tasks | Any | Task list |
| GET | /alerts | Any | Alert list |
| POST | /alerts/:id/acknowledge | Any | Acknowledge alert |
| GET | /incidents | Any | Incident list |
| POST | /incidents | Any | Create incident |
| GET | /prestart/checklist | Any | Pre-populated checklist |
| POST | /prestart/submit | Any | Submit → AUTHORIZED/BLOCKED/REVIEW |
| POST | /ml/predict-eta | Any | ETA prediction |
| POST | /ml/anomaly-check | Any | Anomaly detection |
| POST | /simulator/activate | Engineer+ | Trigger demo scenario |
| POST | /cv/simulate | Engineer+ | Inject CV event |
| POST | /copilot/query | Engineer+ | RAG query |
| WS | /ws?token=... | Any | Real-time events |

---

## 17. Frontend Routes

| Route | Component | Roles | Description |
|-------|-----------|-------|-------------|
| /login | LoginPage | Public | Auth with demo account selector |
| /dashboard | DashboardPage | Engineer/Supervisor/Admin | 7 KPI cards + charts |
| /machines | MachinesPage | Engineer/Supervisor/Admin/Maintenance | Fleet table |
| /machines/:id | MachineDetailPage | Same | Telemetry chart + health drilldown |
| /operators | OperatorsPage | Engineer/Supervisor/Admin/Safety | Operator cards |
| /operators/:id | OperatorDetailPage | Same + own | Operator 360 |
| /tasks | TasksPage | All | Task list with progress |
| /alerts | AlertsPage | All | Alert feed + acknowledge |
| /incidents | IncidentsPage | Engineer/Supervisor/Admin/Safety | Incident log |
| /prestart | PrestartPage | All | Pre-start checklist |
| /dashcam | DashcamPage | Engineer/Supervisor/Admin/Safety | CV events + simulate |
| /training | TrainingPage | All | Training module library |
| /analytics | AnalyticsPage | Engineer/Supervisor/Admin | Productivity + radar |
| /copilot | CopilotPage | Engineer/Admin | AI chatbot |
| /settings | SettingsPage | Engineer/Admin/Supervisor | Demo scenario controls |
| /operator | OperatorDashboardPage | Operator | Simplified task view |
| /watch | WatchPage | All | 14-screen watch simulator |

---

## 18. End-to-End Flows

### Alert flow
```
Telemetry event / CV event / Simulator scenario
  → SafetyEngine.evaluate()
  → Alert INSERT into DB
  → If CRITICAL: Incident INSERT into DB
  → ws_manager.broadcast_alert()
  → All WebSocket clients receive ALERT message
  → Engineer dashboard: alert count increments, feed updates
  → Operator watch: navigates to ActiveAlertScreen, haptic vibration
  → Operator acknowledges on watch → ACKNOWLEDGE_ALERT WS message → DB updated
```

### Pre-start flow
```
Operator selects machine
  → GET /prestart/checklist?machine_id=&operator_id=
  → Backend auto-checks: cert expiry, fuel level, critical faults, health score
  → Returns pre-populated items
  → Operator confirms remaining items in UI
  → POST /prestart/submit
  → Backend: required items all passed? → AUTHORIZED / BLOCKED / REVIEW
  → machine_permissions record created
  → machine.authorization_status updated
```

### ML prediction flow
```
POST /ml/predict-eta with task features
  → ml_service.predict_eta()
  → Encode 14 features (task_type→int, weather→int, etc.)
  → RandomForest.predict([features])
  → Return { predicted_minutes, confidence_interval: [×0.85, ×1.15] }
```

### Demo scenario flow
```
POST /simulator/activate { scenario: "PROXIMITY_HAZARD" }
  → SimulatorService.activate()
  → Fetch first active machine + operator from DB
  → Build telemetry dict with person_distance_m: 3.5
  → SafetyEngine.evaluate_telemetry()
  → PROXIMITY_CRITICAL alert created
  → Incident auto-created (CRITICAL severity)
  → WebSocket broadcast ALERT + SCENARIO_ACTIVATED
  → Dashboard receives → alert count ++
  → Watch receives → navigates to alert screen → vibrate
```

---

## 19. Known Limitations

1. **SQLite concurrency:** Single writer. Use PostgreSQL for >1 concurrent user.
2. **ML trained on synthetic data:** Models are valid architecturally but not calibrated on real CAT telemetry. Performance metrics are on synthetic test data.
3. **Mock RAG:** Copilot returns pre-written answers, not true vector retrieval. ChromaDB integration is designed but not wired.
4. **No Redis:** WebSocket broadcasts are single-process only. Multi-worker deployment needs Redis pub/sub.
5. **No real camera:** CV is fully simulated. Real OpenCV/YOLO integration requires camera hardware.
6. **No real wearable:** Watch is a browser simulator. Real BLE/smartwatch integration is P2.
7. **Biometric data:** All synthetic. Real biometric data requires privacy compliance beyond this demo.

---

## 20. Production Migration Path

1. Set `USE_SQLITE=false`, configure `DATABASE_URL` to PostgreSQL → no code changes
2. Add `REDIS_URL`, swap `ws_manager` broadcast to Redis pub/sub → ~50 lines changed
3. Run `alembic upgrade head` for schema migrations
4. Add `OPENAI_API_KEY` + run `python rag/embeddings/index_documents.py` for real RAG
5. Train models on real telemetry → replace `.joblib` files → backend auto-loads on restart
6. Deploy with `docker compose up` (docker-compose.yml to be created)
7. Configure HTTPS, reverse proxy (nginx), and proper JWT secrets

---

## 21. Demo Script (5-minute version)

1. Open `http://localhost:5173`, login as `engineer@cat.com / demo1234`
2. Point to the 7 KPI cards — click **Machines Active** → show fleet table
3. Click **Safety Score** → show 6 component breakdown
4. Go to **Operators** → click James Mitchell → show Operator 360 (timeline, score, anomaly)
5. Click a machine → Machine Detail → show telemetry chart + health drilldown
6. Open new tab: `http://localhost:5173/watch` → login as `op1001@catsite.com / demo1234`
7. Go back to engineer view → **Settings** → click **PROXIMITY HAZARD**
8. Watch tab automatically navigates to the alert screen and pulses red
9. Go to **Pre-Start** → select EXC001 → show AUTHORIZED flow
10. Go to **AI Copilot** → type "Why is EXC001 showing a hydraulic warning?"

---

## 22. Assumptions

- All biometric/wearable values are synthetic demo data, not real measurements
- Machine fault codes are realistic in structure but not sourced from real CAT documentation
- ETA model trained on synthetic data only — not validated against real site operations
- The "safety score" and "health score" are demo indices for visualisation purposes
- Authentication uses HS256 JWT — production would use RS256 with key rotation
- All times are UTC; timezone display relies on browser locale

---

## 23. Synthetic Data Disclaimer

All data in this system — operators, machines, sites, telemetry, incidents, biometric readings — is **entirely synthetic** and generated programmatically for demonstration purposes.

- No real Caterpillar machine data was used
- No real personal data was used
- No copyrighted Kaggle or third-party datasets were copied
- Data distributions are inspired by publicly documented ranges for heavy equipment telemetry
- The dataset generator is fully reproducible with a fixed seed

---

*CAT MachOps 360 — Built at Caterpillar Hackathon — Synthetic demo data only*
