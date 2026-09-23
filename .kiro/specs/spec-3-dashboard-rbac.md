# Spec 3 — Engineer/Supervisor Dashboard & RBAC

## Status: READY FOR IMPLEMENTATION

---

## Requirements

### REQ-3.1 Login page
- `/login` route accessible without auth
- Email + password form
- JWT stored in memory (not localStorage for security; use httpOnly cookie or in-memory with refresh)
- On login, redirect to `/dashboard` if engineer/supervisor/admin, `/operator` if operator role
- Show role badge after login

### REQ-3.2 Engineer command center dashboard (`/dashboard`)
Top-level overview with 6 clickable KPI cards:
1. **Machines Active** — count active/total, click → machines list with status
2. **Operators Active** — count active/total, click → operators list
3. **Safety Score** — percentage with trend arrow, click → safety breakdown
4. **Machine Health** — percentage, click → fleet health overview
5. **Productivity** — percentage, click → productivity analytics
6. **Active Alerts** — count with severity breakdown, click → alerts list
7. **Incidents Today** — count, click → incidents list

All cards must update in real-time via WebSocket.

### REQ-3.3 Machines Active drilldown
Table with columns: Machine ID, Type, Status, Current Operator, Current Task, Zone, Op Hours, Utilization%, Load%, Alerts.
Row click → `/machines/:id`

### REQ-3.4 Machine Health drilldown
Per-machine health score with expandable sub-scores:
- Engine Health, Fuel Health, Hydraulic Health, Electrical Health, Mechanical Health, Maintenance Status
- Each sub-score shows contributing parameters
- Overall = weighted average

### REQ-3.5 Operators Active drilldown
Table: Operator ID, Name, Machine, Task, Shift, Experience, Safety Score, Cert Status, Wearable, Alerts.
Row click → `/operators/:id` (Operator 360)

### REQ-3.6 Operator 360 profile (`/operators/:id`)
Full-page profile containing:
- Identity: name, employee code, experience, certifications, training completion
- Today's timeline: chronological list of tasks with start/end, duration, estimated vs actual, machine, zone
- Safety events today: proximity, seatbelt, speed violations
- Biometric summary (labelled as "Operational Risk Indicators — not medical diagnoses")
- Anomaly status
- Break history
- Authorization history

### REQ-3.7 RBAC
- 6 roles: operator, supervisor, engineer, safety_officer, maintenance_engineer, admin
- Routes protected at both backend (Depends) and frontend (redirect if insufficient role)
- Role permissions table enforced server-side

### REQ-3.8 Sidebar navigation
Links visible depend on role. Operator sees minimal set. Engineer sees full set.

---

## Design

### Dashboard layout
```
┌─────────────────────────────────────────────────────┐
│ TOPBAR: Logo | Site selector | Alerts bell | User   │
├──────────┬──────────────────────────────────────────┤
│          │  KPI CARDS ROW (7 cards)                 │
│ SIDEBAR  │  ─────────────────────────────────────── │
│          │  MAIN CONTENT (charts + tables)          │
│  nav     │                                          │
│  links   │  Site Map / Machine List / Alert Feed    │
│          │                                          │
└──────────┴──────────────────────────────────────────┘
```

### KPI Card component
```tsx
<KpiCard
  title="Safety Score"
  value="91%"
  trend="+2%"
  trendDir="up"
  severity="success"
  onClick={() => openDrawer('safety')}
  icon={<ShieldIcon />}
/>
```

### RBAC implementation
Backend: `backend/app/core/dependencies.py`
```python
def require_role(roles: list[str]):
    def check(current_user = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return current_user
    return check
```

Frontend: `src/hooks/useAuth.ts` + `src/components/ui/ProtectedRoute.tsx`

### Role permission matrix
| Feature | operator | supervisor | engineer | safety_officer | maintenance | admin |
|---------|----------|------------|----------|----------------|-------------|-------|
| View own data | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| View all operators | - | ✓ | ✓ | ✓ | - | ✓ |
| View all machines | - | ✓ | ✓ | - | ✓ | ✓ |
| Assign tasks | - | ✓ | ✓ | - | - | ✓ |
| View safety analytics | - | ✓ | ✓ | ✓ | - | ✓ |
| Machine config | - | - | ✓ | - | ✓ | ✓ |
| RAG copilot | - | - | ✓ | - | - | ✓ |
| User management | - | - | - | - | - | ✓ |

---

## Tasks

- [ ] Create backend auth router (POST /auth/login, POST /auth/refresh, GET /auth/me)
- [ ] Create backend users router with RBAC
- [ ] Create JWT security utils (backend/app/core/security.py)
- [ ] Create RBAC dependencies (backend/app/core/dependencies.py)
- [ ] Create frontend login page
- [ ] Create frontend auth store (Zustand)
- [ ] Create ProtectedRoute component
- [ ] Create AppLayout with sidebar + topbar
- [ ] Create KpiCard component
- [ ] Create dashboard page with 7 KPI cards
- [ ] Create machines drilldown drawer
- [ ] Create machine health drilldown
- [ ] Create operators drilldown drawer
- [ ] Create Operator 360 page (/operators/:id)
- [ ] Wire role-based sidebar navigation
