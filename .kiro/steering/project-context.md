# CAT MachOps 360 — Project Context

## What This Project Is

CAT Smart Operator Intelligence Platform — an intelligent human-machine operations platform for Caterpillar heavy equipment.

Central concept: **OPERATOR + MACHINE + ENVIRONMENT + TASK → INTELLIGENCE ENGINE → SAFETY + PRODUCTIVITY + PREDICTION + RECOMMENDATION**

The operator is a first-class entity. This is NOT merely a machine dashboard.

## Hackathon Context

- Team: 3 developers
- Time budget: ~4 hours for working MVP
- Priority: P0 working demo > completeness > architectural perfection

## Priority Order

**P0 (must work):**
1. Engineer/Supervisor dashboard
2. Operator dashboard
3. Watch simulator
4. Daily tasks
5. Safety alerts
6. Machine health
7. Operator monitoring
8. Pre-start machine authorization/checklist
9. Task ETA prediction
10. Large realistic synthetic dataset generator
11. Dashcam event integration/simulation
12. RBAC
13. Incident logging
14. Seed/demo data
15. Localhost working end-to-end

**P1 (build if time permits):**
RAG engineer chatbot, ML anomaly detection, personalized training recommendation, advanced dashcam CV, maintenance prediction

**P2 (architecture/docs only):**
Real smartwatch/BLE, real machine telemetry, IoT gateway, streaming infrastructure

## Team Workstreams

- **Member 1** → frontend/ (React dashboard, watch UI, charts)
- **Member 2** → backend/, data/ (FastAPI, PostgreSQL, auth, safety engine)
- **Member 3** → ml/, rag/, cv/ (dataset generator, ETA model, anomaly detection, RAG)

## Demo Story

Login as operator → pre-start checklist → start task → watch shows ETA → proximity alert fires → watch vibrates → engineer sees alert → drill into safety score + machine health + operator 360 → trigger anomaly → ML detects it → RAG copilot answers engineer query → training recommendation shown.
