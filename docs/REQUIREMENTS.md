# Requirements — CAT MachOps 360

## Product Vision

CAT MachOps 360 is an intelligent human-machine operations platform for Caterpillar heavy equipment construction and mining sites.

**Central concept:**
```
OPERATOR + MACHINE + ENVIRONMENT + TASK
              ↓
      INTELLIGENCE ENGINE
              ↓
SAFETY + PRODUCTIVITY + PREDICTION + RECOMMENDATION
```

The system treats the **operator as a first-class entity** — not just a machine driver.

---

## Stakeholders

| Role | Primary Need |
|------|-------------|
| Engineer / Site Manager | Site-wide operational visibility, machine health, productivity analytics |
| Supervisor | Operator assignment, task management, alert oversight |
| Operator | Know their tasks, get safety alerts, perform pre-start checks |
| Safety Officer | Safety score tracking, incident management, training compliance |
| Maintenance Engineer | Machine health, fault codes, maintenance scheduling |

---

## Functional Requirements

### FR-1 Engineer / Supervisor Command Center

**FR-1.1** The system shall display a site-wide command center dashboard with the following KPI cards, each clickable to a detail view:
- Machines Active (count + total)
- Operators Active (count + total)
- Safety Score (site average, with trend)
- Machine Health (fleet average)
- Productivity (task completion rate)
- Active Alerts (count, with severity breakdown)
- Incidents Today (count)

**FR-1.2** Each KPI card shall open a detail drawer or page showing the underlying data.

**FR-1.3** The dashboard shall update in real time via WebSocket — alert counts, KPI values, and machine status shall reflect live changes without page refresh.

---

### FR-2 Machine Monitoring

**FR-2.1** The system shall display a list of all machines with: machine code, type, status, current operator, current task, zone, operating hours, health score, fuel level, alerts.

**FR-2.2** Each machine shall have a health drilldown showing:
- Engine: RPM, temperature, oil pressure, coolant temperature, hours, fault codes
- Fuel: level %, consumption rate, efficiency score
- Hydraulics: pressure, temperature, flow
- Electrical: battery voltage
- Mechanical: vibration, brake status, track condition
- Maintenance: last service, next service due, risk level

**FR-2.3** Machine health shall be expressed as a single overall score (0–100) computed from weighted sub-scores. The score shall be labelled as a demo index, not a certified diagnostic.

**FR-2.4** The system shall display live telemetry charts for active machines.

---

### FR-3 Operator Monitoring

**FR-3.1** The system shall display a list of all operators with: name, employee code, assigned machine, task, shift status, experience level, certification status, safety score, wearable connectivity, continuous operating duration.

**FR-3.2** Each operator shall have an Operator 360 profile containing:
- Full identity and certification details
- Today's complete task timeline with start/end times, durations, estimated vs actual, machine, zone
- Safety events overlaid on the timeline
- Break history
- Biometric/wearable summary (labelled as operational risk indicators — not medical diagnoses)
- Training recommendations
- Anomaly detection status

**FR-3.3** Biometric fields (heart rate, fatigue indicator, attention indicator) shall be clearly labelled as operational risk indicators. The system shall not claim diagnostic accuracy for any health or impairment assessment.

---

### FR-4 Operator Dashboard

**FR-4.1** Operators shall have a simplified dashboard showing: current task, task progress, next task, safety status, active alerts, shift summary.

**FR-4.2** Operators shall see only their own data. They shall not see other operators' profiles or site-wide analytics.

---

### FR-5 Smart Watch Simulator

**FR-5.1** The system shall include a watch simulator page that renders a smartwatch-style UI (max 320px width, dark theme, touch-friendly).

**FR-5.2** The watch shall support 14 navigable screens:
1. Home (time, operator, current task, safety status)
2. Current Task (type, zone, progress bar, ETA)
3. Task Progress (quantity, cycles, estimated completion)
4. Next Task
5. Safety Status
6. Active Alert (with ACKNOWLEDGE button)
7. Break Recommendation
8. Machine Status
9. Emergency (large SOS button)
10. Shift Summary
11. Today's Tasks
12. Safety Events Today
13. QR Code (operator ID only — no sensitive data)
14. Training Reminder

**FR-5.3** When a HIGH or CRITICAL alert fires, the watch shall automatically navigate to the Active Alert screen.

**FR-5.4** The watch shall trigger `navigator.vibrate()` for alert notifications, with visual fallback for unsupported browsers.

**FR-5.5** The QR code shall contain only the operator's ID. No biometric, personal, or sensitive data shall be encoded in the QR.

---

### FR-6 Pre-Start Machine Check

**FR-6.1** Before a machine session begins, an operator or supervisor shall complete a pre-start checklist containing 10 required items and 1 optional item.

**FR-6.2** The system shall automatically check machine health, fuel level, active faults, and certification validity from live data. Items that can be auto-checked shall be pre-populated.

**FR-6.3** The system shall produce one of three authorization outcomes:
- **AUTHORIZED** — all required checks passed
- **BLOCKED** — one or more required checks failed (with reason shown)
- **REVIEW** — optional items not confirmed, or risk indicators elevated

**FR-6.4** Pre-start check results shall be stored with timestamp, operator, machine, items, and authorization outcome.

**FR-6.5** Machine authorization status shall be updated after each pre-start check.

---

### FR-7 Safety Engine

**FR-7.1** The system shall implement a rule-based safety engine that evaluates telemetry and CV events against configurable thresholds.

**FR-7.2** The safety engine shall implement the following rules at minimum:

| Rule | Trigger | Severity |
|------|---------|----------|
| Seatbelt unfastened | Seatbelt off while speed > 0 | HIGH |
| Proximity warning | Person distance < 10m | MEDIUM |
| Proximity critical | Person distance < 5m | CRITICAL |
| Speed violation | Speed > zone limit | HIGH |
| Overload warning | Load > 90% | MEDIUM |
| Overload critical | Load > 100% | CRITICAL |
| Engine temp warning | Temp > 105°C | MEDIUM |
| Engine temp critical | Temp > 115°C | CRITICAL |
| Hydraulic warning | Pressure outside ±20% nominal | MEDIUM |
| Excessive idling | Idle > 15 min | LOW |
| Break recommendation | Continuous operating > 90 min | LOW |
| Dashcam person in zone | Person detected in restricted zone | HIGH |
| Fatigue risk | Fatigue indicator > 0.75 | MEDIUM |

**FR-7.3** All thresholds shall be configurable via environment variables, not hardcoded.

**FR-7.4** Every fired alert shall be stored with: alert_id, timestamp, machine, operator, type, severity, trigger data, message, recommended action, acknowledgement status.

**FR-7.5** CRITICAL alerts shall automatically create an incident record.

**FR-7.6** Every alert shall be broadcast via WebSocket to all connected clients in real time.

---

### FR-8 Alerts

**FR-8.1** The system shall display all alerts in a paginated, filterable list.

**FR-8.2** Operators and supervisors shall be able to acknowledge alerts. Acknowledgements shall be stored with who acknowledged and when.

**FR-8.3** Alert acknowledgement from the watch shall sync to the backend.

---

### FR-9 Incident Management

**FR-9.1** The system shall maintain an incident log with: id, timestamp, site, zone, machine, operator, task, category, severity, description, trigger data, evidence, status, assigned to, resolution, root cause, corrective action.

**FR-9.2** Incidents shall be creatable both automatically (from CRITICAL alerts) and manually.

**FR-9.3** Incident status lifecycle: OPEN → INVESTIGATING → RESOLVED.

---

### FR-10 Task Management and ETA Prediction

**FR-10.1** The system shall display all tasks with: type, machine, operator, progress, estimated and actual duration, status, weather, terrain.

**FR-10.2** The system shall predict task duration using a machine learning model (RandomForestRegressor) trained on: task type, machine type, machine age, operator skill, weather, terrain, load, and historical duration.

**FR-10.3** If the ML model is not available, the system shall return a mock prediction with a clear disclaimer.

**FR-10.4** The operator's watch shall display the AI ETA for the current task.

---

### FR-11 Operator Anomaly Detection

**FR-11.1** The system shall detect unusual operating patterns using an IsolationForest model trained on: speed, acceleration events, idle duration, fuel consumption, engine RPM, load, cycle time.

**FR-11.2** The anomaly result shall be labelled NORMAL or UNUSUAL, with a human-readable reason.

**FR-11.3** Anomaly results shall use neutral language. The system shall not accuse operators of unsafe behaviour — it shall detect and report unusual patterns only.

---

### FR-12 Dashcam / Computer Vision

**FR-12.1** The system shall accept CV events from a pluggable adapter (real camera or simulator).

**FR-12.2** For the demo, a simulated CV adapter shall generate realistic events: person detected, vehicle detected, obstacle detected, restricted zone entry.

**FR-12.3** CV events shall flow through the safety engine and produce alerts identical to those from telemetry events.

**FR-12.4** Attention events (eye closure, yawning) shall be clearly labelled as simulated demo features.

---

### FR-13 Training Hub

**FR-13.1** The system shall maintain a library of training modules with: title, category, type (video/simulation/quiz), duration, mandatory flag.

**FR-13.2** The system shall track operator training completion and scores.

**FR-13.3** The system shall generate personalised training recommendations based on operator incident and alert history.

**FR-13.4** Recommendation triggers:
- 3+ proximity events in 7 days → Proximity Safety Awareness module
- 3+ excessive idle alerts → Fuel Efficient Operation module
- 2+ speed violations → Safe Operating Speeds module
- Certification expiring in 30 days → Certification Renewal module
- Anomaly detected → Advanced Machine Operation module

---

### FR-14 RAG Engineer Copilot

**FR-14.1** Engineers shall have access to an AI copilot that answers queries from synthetic machine manuals, safety guidelines, and maintenance documentation.

**FR-14.2** The copilot shall clearly display a disclaimer on all responses: "Responses generated from synthetic demo documents — not validated CAT documentation."

**FR-14.3** For structured queries (operator training status, machine faults), the copilot shall supplement RAG retrieval with live database queries.

**FR-14.4** The copilot shall operate in mock mode if no LLM provider is configured, returning pre-written realistic responses.

---

### FR-15 RBAC

**FR-15.1** The system shall enforce role-based access control at the API level (not just the frontend).

**FR-15.2** Six roles shall exist: operator, supervisor, engineer, safety_officer, maintenance_engineer, admin.

**FR-15.3** Role permission matrix:

| Capability | operator | supervisor | engineer | safety_officer | maintenance | admin |
|------------|----------|------------|----------|----------------|-------------|-------|
| View own data | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| View all operators | — | ✓ | ✓ | ✓ | — | ✓ |
| View all machines | — | ✓ | ✓ | — | ✓ | ✓ |
| Assign tasks | — | ✓ | ✓ | — | — | ✓ |
| Safety analytics | — | ✓ | ✓ | ✓ | — | ✓ |
| Machine config | — | — | ✓ | — | ✓ | ✓ |
| RAG copilot | — | — | ✓ | — | — | ✓ |
| User management | — | — | — | — | — | ✓ |

---

### FR-16 Demo Scenario Controls

**FR-16.1** Engineers and admins shall have access to a scenario control panel that injects realistic events into the live system.

**FR-16.2** Twelve scenarios shall be available (see README for full list).

**FR-16.3** Activating a scenario shall trigger the full event pipeline: telemetry/CV event → safety engine → alert → WebSocket → dashboard + watch → incident if CRITICAL.

---

## Non-Functional Requirements

**NFR-1 Performance:** The dashboard shall load KPI data within 2 seconds on localhost.

**NFR-2 Real-time:** Alerts shall appear on the dashboard and watch within 1 second of being fired.

**NFR-3 No GPU required:** All ML models shall run on CPU. The demo shall work without CUDA.

**NFR-4 Offline demo:** The core demo shall work without internet access (no external API calls required in mock mode).

**NFR-5 Reproducible data:** Demo data seeding shall be deterministic with seed=42.

**NFR-6 Privacy:** Biometric data shall be labelled as operational risk indicators. The system shall not claim diagnostic accuracy. QR codes shall contain only operator IDs.

**NFR-7 Security:** Passwords shall be hashed (bcrypt). Secrets shall be in environment variables. JWT shall be used for authentication.

**NFR-8 Scalability demonstration:** The dataset generator shall support demo (5k rows), dev (100k rows), and stress (1M+ rows) profiles.

---

## Out of Scope (for this build)

- Real CAT machine CAN bus or telemetry hardware integration
- Real smartwatch / BLE wearable integration
- Real camera / YOLO computer vision (simulated only)
- Real IoT gateway
- Production deployment infrastructure
- Multi-tenant support
- Mobile native app
