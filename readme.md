# CAT MachOps 360 — Smart Operator Intelligence Platform

## 🚀 RUNNING RIGHT NOW
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/api/docs

---

## Quick Start (3 commands)

### Terminal 1 — Backend
```powershell
cd backend
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
```

### Terminal 2 — Frontend
```powershell
cd frontend
npm run dev
```

**That's it.** No PostgreSQL, no Redis, no Docker needed for demo.
Uses SQLite + auto-seeds all demo data on first start.

---

## Demo Login Credentials

| Role | Email | Password |
|------|-------|----------|
| **Engineer** | engineer@cat.com | demo1234 |
| **Supervisor** | supervisor@cat.com | demo1234 |
| **Operator** (James Mitchell) | op1001@catsite.com | demo1234 |
| **Safety Officer** | safety@cat.com | demo1234 |
| **Admin** | admin@cat.com | demo1234 |

---

## Demo Script (for review)

1. Open http://localhost:5173
2. Login as **engineer@cat.com / demo1234**
3. See the Command Center — 7 live KPI cards
4. Click **Machines Active** → see 10 machines with health/fuel/status
5. Click **Operators Active** → see 10 operators with safety scores
6. Click any operator → **Operator 360** page (timeline, safety score, anomaly)
7. Click **Machine Health** card → health drilldown (engine/fuel/hydraulics)
8. Go to **Settings** → Demo Controls → click **PROXIMITY HAZARD**
9. Watch the alert appear in the **Alerts** feed
10. Open a new tab: http://localhost:5173/watch → watch shows the alert
11. Go to **Pre-Start** → select a machine → complete the checklist
12. Go to **AI Copilot** → ask "Why is EXC001 showing a hydraulic warning?"
13. Go to **Dashcam** → click "Person Detected" button → alert fires
14. Go to **Analytics** → productivity + radar charts

---

## What's Built (P0 Complete)

| Feature | Status |
|---------|--------|
| Engineer dashboard + 7 KPI cards | ✅ |
| Operator dashboard | ✅ |
| Watch simulator (14 screens, haptic) | ✅ |
| Machine list + health drilldown | ✅ |
| Operator list + Operator 360 | ✅ |
| Task list + progress | ✅ |
| Alerts feed + acknowledge | ✅ |
| Incidents page | ✅ |
| Pre-start checklist + authorization | ✅ |
| Safety engine (14 rules) | ✅ |
| RBAC (6 roles) | ✅ |
| Demo scenario simulator (12 scenarios) | ✅ |
| AI Copilot (mock RAG) | ✅ |
| Dashcam CV simulation | ✅ |
| Training hub | ✅ |
| Analytics page | ✅ |
| WebSocket real-time alerts | ✅ |
| Demo data auto-seeded | ✅ |
| SQLite (no DB install needed) | ✅ |

---

## Architecture

```
frontend/     React 18 + TypeScript + Vite + Tailwind + Recharts
backend/      FastAPI + SQLAlchemy + SQLite (demo) / PostgreSQL (prod)
ml/           scikit-learn ETA + anomaly (mock mode, train scripts ready)
data/         Dataset generator (demo/dev/stress profiles)
rag/          RAG copilot documents
cv/           Simulated CV event adapter
```

---

## Dataset / Teammate Instructions

**For the demo:** Dataset is auto-seeded by the backend on startup. Nothing extra needed.

**For the large dataset generator (separate teammate task):**
```powershell
cd data
pip install pandas numpy faker pyarrow
python generators/generate_data.py --profile demo --seed 42
python generators/generate_data.py --profile dev --seed 42
python generators/generate_data.py --profile stress --seed 42
```
This is a separate P0 task — the generator scripts need to be built
(the backend demo works without them).

---

## Python Dependencies
```powershell
cd backend
pip install fastapi "uvicorn[standard]" sqlalchemy aiosqlite pydantic pydantic-settings "python-jose[cryptography]" "passlib[bcrypt]" "bcrypt==4.0.1" python-multipart
```

## Frontend Dependencies
```powershell
cd frontend
npm install
```
