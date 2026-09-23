# Task Board — CAT MachOps 360
### 3-Developer Parallel Execution Plan

**Legend:** ✅ Done · 🔄 In Progress · ⬜ Not Started · 🚫 Blocked

---

## Team Assignment

| Member | Role | Branch | Primary Folders |
|--------|------|--------|----------------|
| **Dev 1** | Frontend / UX | `feature/frontend` | `frontend/` |
| **Dev 2** | Backend / Data / Security | `feature/backend` | `backend/`, `data/` |
| **Dev 3** | ML / AI / CV / Dataset | `feature/ai` | `ml/`, `rag/`, `cv/`, `data/generators/` |

---

## WAVE 0 — Foundation (All 3 together, first 20 min)
*Do this together before splitting. Defines the contracts everyone else builds against.*

| # | Task | Owner | Status |
|---|------|-------|--------|
| W0-1 | Create monorepo folder structure | All | ✅ |
| W0-2 | Create `.gitignore` | All | ✅ |
| W0-3 | Create `.kiro/steering/` files (project context, tech stack, conventions) | All | ✅ |
| W0-4 | Create all 9 Spec files in `.kiro/specs/` | All | ✅ |
| W0-5 | Define API contracts (`docs/api-contracts.md`) | Dev 2 | ✅ |
| W0-6 | Define WebSocket event schemas (`docs/event-schemas.md`) | Dev 2 | ✅ |
| W0-7 | Create `docs/REQUIREMENTS.md` | All | ✅ |
| W0-8 | Create `docs/DESIGN.md` | All | ✅ |
| W0-9 | Create `docs/TASKS.md` | All | ✅ |
| W0-10 | Create `README.md` with startup instructions | Dev 2 | ✅ |

---

## WAVE 1 — Core Infrastructure (Parallel, ~1 hour)

### Dev 1 — Frontend Shell

| # | Task | Status | Notes |
|---|------|--------|-------|
| F1-1 | Create Vite + React + TypeScript project | ✅ | `frontend/` |
| F1-2 | Configure Tailwind CSS with CAT colour palette | ✅ | `tailwind.config.ts` |
| F1-3 | Create `src/types/index.ts` — all TypeScript interfaces | ✅ | Mirrors backend schemas |
| F1-4 | Create React Router with all 17 routes (stub pages) | ✅ | `App.tsx` |
| F1-5 | Create `AppLayout` — sidebar nav + role-based links | ✅ | `components/ui/AppLayout.tsx` |
| F1-6 | Create `LoginPage` with demo account quick-select | ✅ | `pages/LoginPage.tsx` |
| F1-7 | Create auth Zustand store | ✅ | `store/authStore.ts` |
| F1-8 | Create `ProtectedRoute` component | ✅ | `components/ui/ProtectedRoute.tsx` |
| F1-9 | Create reusable UI: `KpiCard`, `StatusDot`, `SeverityBadge`, `Drawer`, `PageHeader` | ✅ | `components/ui/` |
| F1-10 | Create `src/services/api.ts` — all API call functions | ✅ | Uses fetch, no Axios |

### Dev 2 — Backend Core

| # | Task | Status | Notes |
|---|------|--------|-------|
| B1-1 | `backend/requirements.txt` | ✅ | |
| B1-2 | `backend/.env` + `.env.example` | ✅ | SQLite mode |
| B1-3 | `app/core/config.py` — all settings + safety thresholds | ✅ | pydantic-settings |
| B1-4 | `app/core/database.py` — async SQLAlchemy, SQLite + PostgreSQL | ✅ | |
| B1-5 | `app/core/security.py` — JWT + bcrypt | ✅ | bcrypt==4.0.1 pinned |
| B1-6 | `app/core/dependencies.py` — RBAC `require_role()` | ✅ | |
| B1-7 | All SQLAlchemy models (24 tables) | ✅ | `app/models/` |
| B1-8 | All Pydantic schemas | ✅ | `app/schemas/` |
| B1-9 | `app/main.py` — FastAPI app factory, routers, WebSocket, health | ✅ | |
| B1-10 | `app/core/seed.py` — auto demo data seeder | ✅ | Runs on startup |
| B1-11 | `app/core/ws_manager.py` — WebSocket connection pool | ✅ | |
| B1-12 | Auth router — POST /auth/login, GET /auth/me | ✅ | |

### Dev 3 — ML/AI Foundation

| # | Task | Status | Notes |
|---|------|--------|-------|
| A1-1 | `app/services/ml_service.py` — mock + real model interface | ✅ | Backend |
| A1-2 | `app/services/safety_engine.py` — 14 rules | ✅ | Backend |
| A1-3 | `app/services/machine_health.py` — weighted score | ✅ | Backend |
| A1-4 | `app/services/scoring.py` — operator safety score | ✅ | Backend |
| A1-5 | `app/services/recommendations.py` — rule-based training recs | ✅ | Backend |
| A1-6 | `data/generators/profiles.py` — demo/dev/stress config | ⬜ | `data/` |
| A1-7 | `data/generators/generate_data.py` — CLI entry point | ⬜ | |
| A1-8 | Site + zone generator | ⬜ | |
| A1-9 | Operator generator (realistic names, certs, skills) | ⬜ | |
| A1-10 | Machine generator (age, model, maintenance history) | ⬜ | |

---

## WAVE 2 — Core APIs + Pages (Parallel, ~1 hour)

### Dev 1 — Dashboard + Key Pages

| # | Task | Status | Notes |
|---|------|--------|-------|
| F2-1 | `DashboardPage` — 7 KPI cards + drawer components | ✅ | |
| F2-2 | `MachinesPage` — table with search + filter | ✅ | |
| F2-3 | `MachineDetailPage` — telemetry chart + health sections | ✅ | |
| F2-4 | `OperatorsPage` — operator cards | ✅ | |
| F2-5 | `OperatorDetailPage` — Operator 360 (timeline, score, anomaly) | ✅ | |
| F2-6 | `AlertsPage` — filter + acknowledge | ✅ | |
| F2-7 | `TasksPage` — progress bars + ETA | ✅ | |
| F2-8 | `IncidentsPage` | ✅ | |
| F2-9 | `useWebSocket` hook — connects, routes to stores | ✅ | |
| F2-10 | Alert + KPI Zustand stores | ✅ | |
| F2-11 | Fix any TypeScript compilation errors | 🔄 | Check browser console |
| F2-12 | Verify all pages render without crash | 🔄 | |

### Dev 2 — Core Backend APIs

| # | Task | Status | Notes |
|---|------|--------|-------|
| B2-1 | Operators router — GET /operators, /:id, /safety-score, /timeline | ✅ | |
| B2-2 | Machines router — GET /machines, /:id, /health, /telemetry | ✅ | |
| B2-3 | Tasks router — GET, POST, PATCH, start, complete | ✅ | |
| B2-4 | Alerts router — GET, acknowledge | ✅ | |
| B2-5 | Incidents router — GET, POST, PATCH | ✅ | |
| B2-6 | Pre-start router — GET checklist, POST submit | ✅ | |
| B2-7 | Analytics router — site-overview, productivity | ✅ | |
| B2-8 | CV router — events, cameras, simulate | ✅ | |
| B2-9 | Training router — modules, operator status | ✅ | |
| B2-10 | ML router — predict-eta, anomaly-check, model-status | ✅ | |
| B2-11 | Simulator router — activate, reset, status | ✅ | |
| B2-12 | Copilot router — query, history | ✅ | Mock mode |
| B2-13 | Wire safety engine → alert creation → WebSocket broadcast | ✅ | |
| B2-14 | CRITICAL alert → auto-create incident | ✅ | |
| B2-15 | Verify all endpoints return correct response shape | 🔄 | Test with API docs |

### Dev 3 — Dataset Generator + ML Training

| # | Task | Status | Notes |
|---|------|--------|-------|
| A2-1 | Task generator (correlated durations) | ⬜ | |
| A2-2 | Telemetry generator (time-series, realistic values) | ⬜ | |
| A2-3 | Safety events + alerts generator | ⬜ | |
| A2-4 | Wearable events generator | ⬜ | |
| A2-5 | Dashcam events generator | ⬜ | |
| A2-6 | Scenario injector (inject specific anomalies into dataset) | ⬜ | |
| A2-7 | SQL writer (INSERT statements) | ⬜ | |
| A2-8 | Parquet writer (telemetry to Parquet) | ⬜ | |
| A2-9 | `ml/training/train_eta.py` — RandomForest ETA model | ⬜ | |
| A2-10 | `ml/training/train_anomaly.py` — IsolationForest | ⬜ | |
| A2-11 | Test: `python generate_data.py --profile demo --seed 42` produces output | ⬜ | |
| A2-12 | Train ETA model on demo dataset, save `.joblib` | ⬜ | |

---

## WAVE 3 — Watch + Pre-Start + Simulation (Parallel, ~45 min)

### Dev 1 — Watch + Operator UX

| # | Task | Status | Notes |
|---|------|--------|-------|
| F3-1 | `WatchPage` — 14-screen smartwatch simulator | ✅ | |
| F3-2 | Watch Zustand store — screen navigation, active alert | ✅ | |
| F3-3 | Alert → watch navigation + haptic vibration | ✅ | |
| F3-4 | QR code screen (qrcode.react) | ✅ | |
| F3-5 | Emergency button screen | ✅ | |
| F3-6 | `OperatorDashboardPage` — simplified operator view | ✅ | |
| F3-7 | `PrestartPage` — checklist UI + authorization result | ✅ | |
| F3-8 | `DashcamPage` — simulated camera feeds + CV event list | ✅ | |
| F3-9 | `TrainingPage` — module cards | ✅ | |
| F3-10 | `AnalyticsPage` — productivity + radar charts | ✅ | |
| F3-11 | `CopilotPage` — chat UI, example queries, sources panel | ✅ | |
| F3-12 | `SettingsPage` — 12 demo scenario buttons | ✅ | |
| F3-13 | Polish: loading states, error states, empty states | 🔄 | |

### Dev 2 — Simulator + Integration

| # | Task | Status | Notes |
|---|------|--------|-------|
| B3-1 | `SimulatorService` — all 12 scenarios | ✅ | |
| B3-2 | PROXIMITY_HAZARD scenario — full pipeline test | ✅ | |
| B3-3 | MACHINE_OVERHEATING scenario | ✅ | |
| B3-4 | SEATBELT_VIOLATION scenario | ✅ | |
| B3-5 | DASHCAM_PERSON_DETECTION scenario | ✅ | |
| B3-6 | PRESTART_FAILURE scenario (cert expired) | ✅ | |
| B3-7 | UNUSUAL_OPERATOR_BEHAVIOUR scenario | ✅ | |
| B3-8 | Verify WebSocket broadcast reaches frontend | 🔄 | Open /ws in API docs |
| B3-9 | Verify alert → watch push flow end-to-end | 🔄 | |
| B3-10 | Verify pre-start BLOCKED when cert expired | 🔄 | |

### Dev 3 — RAG + CV Adapter

| # | Task | Status | Notes |
|---|------|--------|-------|
| A3-1 | Create synthetic RAG documents (6 markdown files) | ⬜ | `rag/documents/` |
| A3-2 | `rag/retrieval/mock_llm.py` — pre-written realistic answers | ⬜ | |
| A3-3 | `rag/retrieval/rag_service.py` — ChromaDB + mock LLM | ⬜ | |
| A3-4 | Connect rag_service to copilot router | ⬜ | |
| A3-5 | `cv/adapters/base.py` — CVEvent dataclass + CVAdapter ABC | ⬜ | |
| A3-6 | `cv/simulator/simulated_cv_adapter.py` | ⬜ | |
| A3-7 | `ml/inference/predict_eta.py` — inference wrapper | ⬜ | |
| A3-8 | `ml/inference/predict_anomaly.py` — inference wrapper | ⬜ | |
| A3-9 | Verify `python generate_data.py --profile dev` works | ⬜ | |

---

## WAVE 4 — Integration + Polish (All together, ~45 min)

| # | Task | Owner | Status |
|---|------|-------|--------|
| I4-1 | End-to-end demo walkthrough — follow README demo script | All | 🔄 |
| I4-2 | Fix any API response shape mismatches | Dev 2 | 🔄 |
| I4-3 | Fix any TypeScript type errors in frontend | Dev 1 | 🔄 |
| I4-4 | Verify all 12 demo scenarios produce visible results | Dev 2 | 🔄 |
| I4-5 | Verify watch receives alert on PROXIMITY_HAZARD scenario | Dev 1 + Dev 2 | 🔄 |
| I4-6 | Verify pre-start BLOCKED flow works in UI | Dev 1 + Dev 2 | 🔄 |
| I4-7 | Verify AI copilot returns answers | Dev 1 + Dev 3 | 🔄 |
| I4-8 | Verify operator 360 page loads with timeline | Dev 1 + Dev 2 | 🔄 |
| I4-9 | Verify machine health drilldown shows all sections | Dev 1 + Dev 2 | 🔄 |
| I4-10 | Run `python generate_data.py --profile demo` successfully | Dev 3 | 🔄 |
| I4-11 | Train ETA model, verify backend loads it | Dev 3 + Dev 2 | ⬜ |
| I4-12 | Polish login page — make sure demo accounts work | Dev 1 | 🔄 |
| I4-13 | Update `project_explained.md` | Dev 2 | ⬜ |
| I4-14 | Final README check — startup instructions accurate | All | 🔄 |

---

## WAVE 5 — Stretch Goals (if time permits)

### P1 Features

| # | Task | Owner | Status |
|---|------|-------|--------|
| S5-1 | Train real ML models on generated dataset | Dev 3 | ⬜ |
| S5-2 | Integrate real ChromaDB RAG (not just mock) | Dev 3 | ⬜ |
| S5-3 | Add maintenance prediction model | Dev 3 | ⬜ |
| S5-4 | Personalized training recommendations from ML (not just rules) | Dev 3 | ⬜ |
| S5-5 | Docker compose — one command startup | Dev 2 | ⬜ |
| S5-6 | Advanced dashcam CV (real video file processing) | Dev 3 | ⬜ |
| S5-7 | Operator productivity trend charts | Dev 1 | ⬜ |
| S5-8 | Site map / zone visualisation | Dev 1 | ⬜ |
| S5-9 | More detailed maintenance scheduling UI | Dev 1 | ⬜ |
| S5-10 | Audit log viewer | Dev 1 + Dev 2 | ⬜ |

---

## Shared Contracts (do not break these)

These are agreed between all developers. Changes require team discussion.

### API response shape
```json
{ "data": <payload>, "meta": { "timestamp": "ISO8601", "total": <int> } }
```

### Alert severity levels
`LOW` · `MEDIUM` · `HIGH` · `CRITICAL`

### WebSocket message format
```json
{ "type": "ALERT|KPI_UPDATE|TELEMETRY_UPDATE|TASK_UPDATE|...", "payload": {} }
```

### Safety score label
Always: `"Operational Safety Score (Demo Index)"` — never claim validated accuracy.

### Biometric disclaimer
Any field ending in `_risk_indicator` must be labelled:
`"Operational risk indicator — not a medical diagnosis"`

### QR code content
Only: `{ "operator_id": "<uuid>" }` — no personal, biometric, or sensitive data.

---

## Definition of Done (for review)

The following must all pass before claiming a feature complete:

- [ ] Endpoint returns 200 with correct response shape
- [ ] Frontend page renders without console errors
- [ ] RBAC: wrong-role request returns 403
- [ ] Demo data is visible in the page
- [ ] Clickable cards open detail views
- [ ] No hardcoded secrets in committed code
- [ ] Loading states and error states handled

---

## Current Blockers

| # | Blocker | Affects | Owner | Resolution |
|---|---------|---------|-------|-----------|
| None at time of writing | — | — | — | — |

---

## Git Workflow

```bash
# Each dev works on their feature branch
git checkout -b feature/frontend    # Dev 1
git checkout -b feature/backend     # Dev 2
git checkout -b feature/ai          # Dev 3

# Commit frequently
git commit -m "feat(frontend): add machine health drilldown"
git commit -m "feat(backend): wire safety engine to WebSocket"
git commit -m "feat(ai): implement ETA training script"

# Merge to dev when wave is complete
git checkout dev
git merge feature/backend

# main only for demo-ready builds
git checkout main
git merge dev
```

### Commit message prefixes
- `feat(frontend):` — new frontend feature
- `feat(backend):` — new backend feature  
- `feat(ai):` — ML/AI/dataset work
- `fix:` — bug fix
- `docs:` — documentation only
- `test:` — tests only
