# Spec 9 — Integration, Demo Controls & Final Verification

## Status: READY — Execute last

---

## Requirements

### REQ-9.1 Demo scenario control panel
`/settings` page (engineer/admin only) contains a "Demo Controls" section:
- Dropdown to select scenario
- "Activate Scenario" button
- Real-time status: what the scenario injected
- "Reset to Normal" button

Scenarios:
1. NORMAL_OPERATION — steady-state telemetry
2. PROXIMITY_HAZARD — person at 3.5m, CRITICAL alert fires
3. SEATBELT_VIOLATION — seatbelt unfastened while moving
4. EXCESSIVE_IDLING — 25 min idle, LOW alert
5. MACHINE_OVERHEATING — engine temp 118°C, CRITICAL alert
6. HYDRAULIC_ANOMALY — pressure drop 40%, MEDIUM alert
7. UNUSUAL_OPERATOR_BEHAVIOUR — anomaly detected, UNUSUAL flag
8. EXTENDED_SHIFT — 110 min continuous operation, break recommendation
9. DASHCAM_PERSON_DETECTION — CV event, CRITICAL proximity
10. PRESTART_FAILURE — cert expired, BLOCKED authorization
11. MAINTENANCE_WARNING — service overdue, MEDIUM alert
12. TASK_DELAY_WEATHER — heavy rain, ETA increases by 35%

### REQ-9.2 Simulator endpoint
```
POST /simulator/activate
  body: { "scenario": str, "machine_id": str?, "operator_id": str? }
  → injects telemetry/events into the pipeline
  → safety engine evaluates
  → alerts fire
  → WebSocket broadcasts
  → watch receives if applicable

POST /simulator/reset
  → clears injected scenario state

GET /simulator/status
  → current active scenario, injected events count
```

### REQ-9.3 WebSocket real-time flow (complete)
```
ws://localhost:8000/ws?token=<jwt>

Server → Client message types:
  ALERT          { alert: Alert }
  TELEMETRY      { machine_id, readings: TelemetrySummary }
  TASK_UPDATE    { task: Task }
  OPERATOR_UPDATE { operator: OperatorSummary }
  INCIDENT       { incident: Incident }
  SCENARIO_EVENT { scenario: str, description: str }
  PING           { ts: str }

Client → Server:
  ACKNOWLEDGE_ALERT  { alert_id: str }
  SUBSCRIBE         { channels: str[] }
  PONG              { ts: str }
```

### REQ-9.4 End-to-end demo test
`backend/tests/test_e2e_demo.py` — pytest script that:
1. Authenticates as engineer
2. Authenticates as operator
3. Runs pre-start checklist (AUTHORIZED)
4. Activates PROXIMITY_HAZARD scenario
5. Checks alert was created
6. Acknowledges alert as operator
7. Checks incident was created
8. Checks safety score updated
9. Requests ETA prediction
10. Requests anomaly check

### REQ-9.5 Health endpoint
`GET /health` returns:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected",
  "ml_models": { "eta": "loaded", "anomaly": "loaded" },
  "demo_data": "seeded"
}
```

### REQ-9.6 Final checklist verification
All items from "42. Final Acceptance Criteria" in master prompt must pass.

---

## Design

### Demo flow walkthrough (scripted demo path)
```
1. Open http://localhost:5173
2. Login: engineer@cat.com / demo1234
3. Dashboard loads with 7 KPI cards (all showing data)
4. Click "Active Alerts" card → alerts list
5. Open new tab: http://localhost:5173/watch
6. Login: operator@cat.com / demo1234
7. Watch shows home screen: task + ETA
8. Back to engineer dashboard
9. POST /simulator/activate { scenario: "PROXIMITY_HAZARD" }
10. Watch vibrates, navigates to alert screen
11. Engineer dashboard alert count increments
12. Acknowledge on watch
13. Click Operator → Operator 360 page
14. Click Machine Health → drilldown
15. POST /simulator/activate { scenario: "UNUSUAL_OPERATOR_BEHAVIOUR" }
16. Anomaly badge appears on operator card
17. Open /copilot, ask: "Why is EXC001 showing a hydraulic warning?"
18. RAG returns answer with sources
19. Training recommendation shown
20. Open /analytics → productivity + fuel efficiency charts
```

### Startup sequence
```bash
# Terminal 1: infrastructure
docker compose up postgres redis

# Terminal 2: backend
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 3: frontend
cd frontend
npm run dev

# Once (seed data):
cd backend
python -m app.core.seed  # or:
cd data
python generators/generate_data.py --profile demo --seed 42
```

---

## Tasks

- [ ] Create simulator router (POST /simulator/activate, reset, status)
- [ ] Create simulator service (scenario injection)
- [ ] Implement all 12 scenarios in simulator
- [ ] Create WebSocket manager (connection pool + broadcast)
- [ ] Wire all event types to WebSocket
- [ ] Create demo controls panel in /settings
- [ ] Create backend/tests/test_e2e_demo.py
- [ ] Verify all 42 acceptance criteria
- [ ] Update /health endpoint with full system status
- [ ] Write final README with exact startup commands
- [ ] Run full demo walkthrough and fix any issues
- [ ] Update project_explained.md
