# CAT MachOps 360
### Smart Operator Intelligence Platform — Caterpillar Hackathon

> **OPERATOR + MACHINE + ENVIRONMENT + TASK → INTELLIGENCE ENGINE → SAFETY + PRODUCTIVITY + PREDICTION + RECOMMENDATION**

The operator is a first-class entity. This is not a machine dashboard — it is a unified human-machine intelligence platform.

---

## Live URLs (after startup)

| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **Backend API** | http://localhost:8000 |
| **API Docs (Swagger)** | http://localhost:8000/api/docs |
| **Health check** | http://localhost:8000/health |

---

## Prerequisites

| Tool | Minimum version | Check |
|------|----------------|-------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

No PostgreSQL, Redis, or Docker required for the demo. Uses **SQLite** with automatic data seeding.

---

## Installation

### Step 1 — Clone

```bash
git clone <repo-url>
cd "CAT MachOps 360"
```

### Step 2 — Backend dependencies

```powershell
cd backend
pip install fastapi "uvicorn[standard]" sqlalchemy aiosqlite pydantic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt==4.0.1" python-multipart scikit-learn pandas numpy joblib faker
```

> **Important:** Pin `bcrypt==4.0.1`. Newer versions break passlib compatibility.

### Step 3 — Backend environment

The `.env` file is already included and pre-configured for SQLite demo mode.

If it is missing, create `backend/.env` with:
```env
USE_SQLITE=true
SQLITE_URL=sqlite+aiosqlite:///./machops360_demo.db
JWT_SECRET_KEY=cat-machops-360-demo-secret-key-hackathon-2024
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=120
APP_ENV=development
APP_VERSION=1.0.0
FRONTEND_ORIGIN=http://localhost:5173
LLM_PROVIDER=mock
AUTO_SEED_ON_STARTUP=true
```

### Step 4 — Frontend dependencies

```powershell
cd frontend
npm install
```

---

## Starting the Application

Open **two terminals** at the project root.

### Terminal 1 — Backend

```powershell
cd backend
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

Expected startup output:
```
INFO:app.core.seed:Seeding demo data...
INFO:app.core.seed:Demo data seeded successfully.
INFO:app.services.ml_service:ETA model loaded from ../ml/models/eta_model.joblib
INFO:app.services.ml_service:Anomaly model loaded from ../ml/models/anomaly_model.joblib
INFO:app.main:Server ready. ENV=development DB=SQLite
INFO:     Application startup complete.
```

### Terminal 2 — Frontend

```powershell
cd frontend
npm run dev
```

Expected output:
```
VITE v5.x  ready in ~2000ms
➜  Local:   http://localhost:5173/
```

### Open in browser

**http://localhost:5173**

---

## Demo Login Credentials

All passwords: `demo1234`

| Role | Email | What you see |
|------|-------|-------------|
| **Engineer** ← *start here* | engineer@cat.com | Full platform — all 7 KPI cards |
| Supervisor | supervisor@cat.com | Operators, machines, tasks, alerts |
| Safety Officer | safety@cat.com | Safety analytics, incidents, training |
| Maintenance Engineer | maintenance@cat.com | Machine health, faults |
| Admin | admin@cat.com | Everything + settings |
| **Operator** ← *for watch demo* | op1001@catsite.com | Simplified dashboard + watch |

---

## Data Seeding

### Automatic (default — nothing to do)

On first startup, the backend seeds **all demo data automatically**:

| Entity | Count |
|--------|-------|
| Sites | 2 (Alpha Construction, Beta Mining) |
| Machines | 10 (EXC001–EXC004, BUL001–BUL003, LDR001–LDR003) |
| Operators | 10 (James Mitchell, Sarah Chen, David Williams, …) |
| Tasks | 20 (last 8 hours, mix of completed + in-progress) |
| Telemetry | 1,680 rows (24 readings × 7 active machines) |
| Alerts | 4 (proximity, seatbelt, idling, engine temp) |
| Incidents | 1 (proximity — investigating) |
| Training modules | 10 |
| Dashcam events | 5 |

Seeding is **idempotent** — it skips if data already exists.

### Manual re-seed (fresh start)

```powershell
cd backend
Remove-Item -Force machops360_demo.db   # Windows PowerShell
# or: rm machops360_demo.db             # bash/zsh

uvicorn app.main:app --reload --port 8000   # restarts and re-seeds
```

### Large dataset generator

For demonstrating enterprise scalability:

```powershell
# Install extra dependencies
pip install faker pyarrow

# Demo profile (~1.2k telemetry rows, instant)
python data/generators/generate_data.py --profile demo --seed 42

# Dev profile (~144k rows, ~30 seconds)
python data/generators/generate_data.py --profile dev --seed 42

# Stress profile (~2M rows, ~5-10 minutes)
python data/generators/generate_data.py --profile stress --seed 42

# List available profiles
python data/generators/generate_data.py --list-profiles
```

Output:
- `data/seed/<profile>_seed.sql` — SQL INSERTs for all entities
- `data/generated/<profile>_telemetry.parquet` — time-series telemetry
- `data/generated/<profile>_wearable_events.parquet` — biometric events

The backend demo does **not** require these files — it uses its own auto-seeder.

---

## Training ML Models

Models are already **pre-trained** and included in `ml/models/`. The backend loads them automatically.

To retrain from scratch:

```powershell
pip install scikit-learn pandas numpy joblib

# ETA prediction model (RandomForest, ~10 seconds)
python ml/training/train_eta.py --synthetic --samples 5000

# Anomaly detection model (IsolationForest, ~15 seconds)
python ml/training/train_anomaly.py --synthetic --samples 10000
```

Expected output:
```
ETA model:    R²=0.865 | MAE=12.3 min | Saved to ml/models/eta_model.joblib
Anomaly model: 5% anomaly rate | Saved to ml/models/anomaly_model.joblib
```

After training, restart the backend — it auto-loads the new models.

---

## Demo Walkthrough (5 minutes)

### Scene 1 — Command Center
1. Login as `engineer@cat.com`
2. See 7 KPI cards: Machines, Operators, Safety Score, Machine Health, Productivity, Alerts, Incidents
3. Click **Machines Active** → fleet table with health/fuel/temp/operator
4. Click **Safety Score** → 6-component breakdown with progress bars
5. Click **Machine Health** → per-machine health scores

### Scene 2 — Operator Intelligence
6. Go to **Operators** → click **James Mitchell**
7. See Operator 360: today's timeline, safety score components, ML anomaly status, training recommendations

### Scene 3 — Machine Health Drilldown
8. Go to **Machines** → click **EXC001**
9. See live telemetry chart
10. Expand **Engine** section → RPM, temp, oil pressure, hours
11. Expand **Maintenance** section → last service, next due

### Scene 4 — Real-time Alert Demo
12. Open new tab: `http://localhost:5173/watch`
13. Login as `op1001@catsite.com` → watch shows home screen with task ETA
14. Back in engineer tab → go to **Settings** → click **PROXIMITY HAZARD**
15. Watch automatically navigates to the alert screen + red pulse animation
16. Acknowledge on the watch → alert marked acknowledged in both views

### Scene 5 — Pre-Start Authorization
17. Go to **Pre-Start**
18. Select machine EXC001, operator OP1001
19. See auto-populated checklist (fuel, health, cert all checked)
20. Submit → **AUTHORIZED** result

### Scene 6 — AI & Analytics
21. Go to **AI Copilot** → ask: *"Why is EXC001 showing a hydraulic warning?"*
22. See answer with source references + disclaimer
23. Go to **Analytics** → productivity metrics + operational radar chart
24. Go to **Dashcam** → click **Person Detected** button → alert fires → watch notified

---

## Demo Scenarios

Available in **Settings → Demo Controls**. Each triggers the full alert pipeline (telemetry → safety engine → alert → WebSocket → dashboard + watch).

| Scenario | Trigger | Result |
|----------|---------|--------|
| **Proximity Hazard** | Person at 3.5m | CRITICAL alert → watch alert screen |
| Seatbelt Violation | Seatbelt off + moving | HIGH alert |
| Excessive Idling | 25 min idle | LOW alert |
| **Machine Overheating** | Engine 118°C | CRITICAL alert → incident created |
| Hydraulic Anomaly | Pressure drop 40% | MEDIUM alert |
| Unusual Operator Behaviour | Anomaly pattern injected | UNUSUAL flag on operator |
| Extended Shift | 110 min continuous | Break recommendation alert |
| **Dashcam Person Detection** | Person in restricted zone | CRITICAL alert → incident |
| Pre-Start Failure | Cert expired flag set | BLOCKED on next pre-start |
| Maintenance Warning | Fault E-HYD-042 injected | MEDIUM fault alert |
| Task Delay — Weather | Heavy rain flag | ETA +35% on active task |
| Normal Operation | Reset | Clears all injected state |

---

## Project Structure

```
CAT MachOps 360/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app, routers, WebSocket, startup
│   │   ├── core/
│   │   │   ├── config.py              # All settings + safety thresholds (env-driven)
│   │   │   ├── database.py            # Async SQLAlchemy (SQLite/PostgreSQL)
│   │   │   ├── security.py            # JWT + bcrypt
│   │   │   ├── dependencies.py        # require_role(), get_current_user()
│   │   │   ├── seed.py                # Auto demo data seeder
│   │   │   └── ws_manager.py          # WebSocket connection pool + broadcaster
│   │   ├── models/                    # SQLAlchemy ORM (24 tables)
│   │   ├── schemas/                   # Pydantic v2 request/response schemas
│   │   ├── routers/                   # One router per domain (13 routers)
│   │   └── services/
│   │       ├── safety_engine.py       # 14 deterministic safety rules
│   │       ├── machine_health.py      # Weighted health score (6 components)
│   │       ├── scoring.py             # Operator safety score (6 components)
│   │       ├── ml_service.py          # ETA + anomaly (real or mock)
│   │       ├── operator_service.py    # Daily timeline builder
│   │       ├── recommendations.py     # Rule-based training recommendations
│   │       ├── simulator_service.py   # 12 demo scenarios
│   │       ├── alert_service.py       # Alert acknowledgement via WS
│   │       └── cv_service.py          # CV event adapter wiring
│   ├── .env                           # SQLite demo config (not committed in prod)
│   ├── .env.example                   # Template for all settings
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                     # 17 route-level components
│   │   ├── components/ui/             # KpiCard, Drawer, StatusDot, etc.
│   │   ├── hooks/useWebSocket.ts      # WS connection → Zustand stores
│   │   ├── services/api.ts            # All API call functions (no Axios)
│   │   ├── store/                     # authStore, alertStore, watchStore, kpiStore
│   │   └── types/index.ts             # TypeScript interfaces
│   ├── package.json
│   ├── vite.config.ts                 # Proxy /api and /ws to :8000
│   ├── tailwind.config.ts
│   ├── Dockerfile
│   └── nginx.conf
├── ml/
│   ├── models/
│   │   ├── eta_model.joblib           # RandomForest ETA (R²=0.865, MAE=12min)
│   │   └── anomaly_model.joblib       # IsolationForest anomaly detector
│   └── training/
│       ├── train_eta.py               # ETA training script
│       └── train_anomaly.py           # Anomaly training script
├── data/
│   ├── generators/
│   │   ├── generate_data.py           # CLI entry point (--profile demo|dev|stress)
│   │   ├── profiles.py                # Profile configurations
│   │   ├── entity_generators.py       # Sites, zones, machines, operators
│   │   ├── telemetry_generator.py     # Correlated time-series generation
│   │   ├── task_generator.py          # Tasks, alerts, incidents, dashcam
│   │   ├── user_generator.py          # Auth users + certifications
│   │   └── writers.py                 # SQL + Parquet output writers
│   ├── seed/                          # Generated SQL seed files (small ones committed)
│   └── generated/                     # Large Parquet files (gitignored)
├── rag/
│   └── documents/                     # Synthetic CAT documentation for RAG
├── cv/
│   ├── adapters/base.py               # CVEvent dataclass + CVAdapter ABC
│   └── simulator/                     # Simulated CV adapter
├── docs/
│   ├── REQUIREMENTS.md                # 16 functional requirement groups
│   ├── DESIGN.md                      # Architecture, flows, decisions
│   ├── TASKS.md                       # Wave-based team task board
│   ├── api-contracts.md               # All API endpoint contracts
│   └── event-schemas.md               # WebSocket event schemas
├── project_explained.md               # Complete technical reference
├── docker-compose.yml                 # Full stack Docker setup
├── .gitignore
└── README.md
```

---

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Frontend | React 18 + TypeScript | Component model, type safety |
| Build | Vite 5 | Fast HMR, built-in proxy to backend |
| Styling | Tailwind CSS | Industrial dark UI, no custom CSS |
| Charts | Recharts | Lightweight, composable, no WebGL |
| State | Zustand + React Query | Simple global state + server caching |
| QR codes | qrcode.react | Operator ID QR on watch screen |
| Backend | FastAPI | Async, auto-docs, Pydantic v2 validation |
| ORM | SQLAlchemy 2.0 async | Works with both SQLite and PostgreSQL |
| Database (demo) | SQLite / aiosqlite | Zero install, auto-seeded |
| Database (prod) | PostgreSQL 15 | Switch with one env var change |
| Auth | python-jose + passlib + bcrypt | JWT + bcrypt, industry standard |
| ML | scikit-learn 1.8 | CPU-only, interpretable, no GPU needed |
| Data generation | pandas + pyarrow + Faker | Parquet output, realistic fake data |
| Real-time | FastAPI WebSocket | Built-in, no extra broker needed for demo |

---

## Switching to PostgreSQL

```bash
# backend/.env
USE_SQLITE=false
DATABASE_URL=postgresql+asyncpg://cat:cat_secret@localhost:5432/machops360

# Install asyncpg
pip install asyncpg

# Start PostgreSQL
docker compose up postgres redis

# Run backend (will auto-create tables + seed)
cd backend && uvicorn app.main:app --reload --port 8000
```

---

## Enabling Real RAG (OpenAI)

```bash
# backend/.env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

pip install openai sentence-transformers chromadb
python rag/embeddings/index_documents.py
```

---

## Full Docker Stack

```bash
# Copy .env.example to .env and set JWT_SECRET_KEY
cp backend/.env.example backend/.env

docker compose up --build
```

Services started:
- PostgreSQL on :5432
- Redis on :6379
- Backend on :8000
- Frontend on :5173 (nginx)

---

## Team

| Member | Role | Branch |
|--------|------|--------|
| Dev 1 | Frontend, UX, Watch, Charts | `feature/frontend` |
| Dev 2 | Backend, APIs, Safety Engine, Auth | `feature/backend` |
| Dev 3 | ML, Dataset Generator, RAG, CV | `feature/ai` |

---

## Docs

| File | Contents |
|------|---------|
| `docs/REQUIREMENTS.md` | 16 functional requirement groups |
| `docs/DESIGN.md` | Architecture diagrams, data flows, decisions |
| `docs/TASKS.md` | Wave-based task board for all 3 developers |
| `docs/api-contracts.md` | Full API endpoint reference |
| `docs/event-schemas.md` | WebSocket message formats |
| `project_explained.md` | Complete technical deep-dive for judges |

---

*CAT MachOps 360 — Hackathon Demo Build — All data is synthetic — Not validated CAT documentation*
