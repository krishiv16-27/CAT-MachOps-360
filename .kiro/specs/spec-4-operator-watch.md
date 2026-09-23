# Spec 4 — Operator Dashboard & Watch Simulator

## Status: READY FOR IMPLEMENTATION

---

## Requirements

### REQ-4.1 Operator dashboard (`/operator`)
The operator sees a simplified, task-focused view:
- Current assigned machine (status, health summary)
- Current task (type, zone, progress bar, ETA)
- Next task (type, estimated start)
- Safety status (colour-coded: GREEN / AMBER / RED)
- Active alerts (count + most recent)
- Today's completed tasks (count)
- Shift summary (hours worked, breaks taken)
- Quick actions: Start Pre-Start Check, Report Incident, Request Break, View Training

### REQ-4.2 Watch simulator page (`/watch`)
- Renders a smartwatch-shaped UI: max 320px wide, dark background, rounded corners
- Navigable via "screen" buttons (swipe left/right simulation via prev/next buttons)
- Independent from the main dashboard layout — standalone watchface

#### Watch screens (14 screens total):
1. **Home** — time, operator name, task name, progress, ETA, machine status, safety status
2. **Current Task** — task type, zone, progress bar, start time, ETA, machine ID
3. **Task Progress** — quantity completed/target, cycles, estimated completion time
4. **Next Task** — next task type, estimated start, machine, zone
5. **Safety Status** — current safety level, last alert, safety score today
6. **Active Alert** — alert type, severity, message, ACKNOWLEDGE button
7. **Break Recommendation** — continuous operating time, recommended break duration
8. **Machine Status** — machine ID, engine status, fuel level, hydraulic status
9. **Emergency** — large red EMERGENCY button, confirmation screen
10. **Shift Summary** — shift start, elapsed, tasks done, safety events
11. **Today's Tasks** — compact list of completed tasks with times
12. **Safety Events Today** — list of safety events with type + time
13. **QR Code** — operator QR code (contains only operator_id)
14. **Training Reminder** — pending training modules with due dates

### REQ-4.3 Alert on watch
When a HIGH or CRITICAL alert fires:
- Watch automatically navigates to "Active Alert" screen
- Visual pulse animation (CSS) on the alert screen
- Large high-contrast text
- ACKNOWLEDGE button sends acknowledgement to backend
- After acknowledge: returns to previous screen, alert marked acknowledged

### REQ-4.4 Haptic / vibration simulation
- When CRITICAL alert fires: `navigator.vibrate([500, 100, 500])` if supported
- Visual fallback: red border pulse animation on watch frame

### REQ-4.5 QR operator identification
- QR contains only: `{ "operator_id": "OP1001", "token": "<short-lived token>" }`
- No biometric, personal, or sensitive data in QR
- Rendered via qrcode.react on the watch QR screen

### REQ-4.6 Operator 360 daily timeline
- Accessible from operator dashboard and from engineer's Operator 360 page
- Chronological list of all tasks today
- Each task shows: start time, end time, duration, estimated duration, machine, zone, status
- Safety events overlaid on timeline
- Break periods shown
- Totals: operating time, idle time, fuel used

---

## Design

### Watch component structure
```
WatchSimulator (page)
  └── WatchFrame (320px, rounded, dark bg, simulated bezel)
        ├── WatchScreen (current active screen)
        │     ├── HomeScreen
        │     ├── CurrentTaskScreen
        │     ├── ActiveAlertScreen (shown on HIGH/CRITICAL alert)
        │     ├── QRScreen
        │     └── ... (11 more screens)
        ├── WatchNavDots (screen indicator dots)
        └── WatchNavButtons (prev/next)
```

### Watch state
Managed in `src/store/watchStore.ts` (Zustand):
```ts
{
  currentScreen: number,
  screens: WatchScreen[],
  activeAlert: Alert | null,
  operator: Operator,
  currentTask: Task | null,
  machineStatus: MachineSummary | null,
  shiftSummary: ShiftSummary,
  navigateTo: (screen: number) => void,
  acknowledgeAlert: (alertId: string) => void,
}
```

### Alert flow to watch
```
Backend alert event
  → WebSocket message { type: "ALERT", payload: Alert }
  → useWebSocket hook
  → alertStore.addAlert(alert)
  → watchStore.setActiveAlert(alert) if severity HIGH|CRITICAL
  → WatchSimulator re-renders to ActiveAlertScreen
  → navigator.vibrate() called
```

### Watch visual spec
- Background: `#0f172a` (slate-900)
- Frame: 2px `#f59e0b` (amber-500) border, 40px border-radius
- Text primary: white, 18px+
- Status GREEN: `#4ade80`
- Status AMBER: `#fbbf24`
- Status RED: `#f87171`
- Alert screen: full red background `#7f1d1d`, pulsing border

---

## Tasks

- [ ] Create operator dashboard page (/operator)
- [ ] Create operator task card component
- [ ] Create shift summary component
- [ ] Create WatchSimulator page (/watch)
- [ ] Create WatchFrame component
- [ ] Create all 14 watch screen components
- [ ] Create watchStore (Zustand)
- [ ] Create watch navigation (prev/next + dots)
- [ ] Implement alert → watch navigation flow
- [ ] Implement haptic vibration + visual fallback
- [ ] Implement QR screen with qrcode.react
- [ ] Implement ACKNOWLEDGE button + API call
- [ ] Create operator daily timeline component
- [ ] Wire watch to WebSocket alert events
