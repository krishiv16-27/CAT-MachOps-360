// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  user_id: string
  email: string
  name: string
  role: UserRole
  operator_id: string | null
}

export type UserRole =
  | 'operator'
  | 'supervisor'
  | 'engineer'
  | 'safety_officer'
  | 'maintenance_engineer'
  | 'admin'

// ── Operator ──────────────────────────────────────────────────────────────────
export interface OperatorSummary {
  operator_id: string
  employee_code: string
  name: string
  experience_years: number
  skill_level: number
  certification: string | null
  certification_expiry: string | null
  current_machine_id: string | null
  current_task_id: string | null
  shift_status: 'ON_SHIFT' | 'OFF_SHIFT' | 'ON_BREAK'
  safety_score: number
  authorization_status: string
  continuous_operating_minutes: number
  site_id: string | null
}

export interface TimelineEntry {
  entry_type: 'TASK' | 'BREAK' | 'SAFETY_EVENT'
  start_time: string
  end_time: string | null
  duration_minutes: number | null
  label: string
  machine_id: string | null
  zone_id: string | null
  status: string | null
  metadata?: Record<string, unknown>
}

// ── Machine ───────────────────────────────────────────────────────────────────
export interface MachineSummary {
  machine_id: string
  machine_code: string
  machine_type: string
  model_name: string
  site_id: string | null
  zone_id: string | null
  status: 'ACTIVE' | 'INACTIVE' | 'MAINTENANCE' | 'FAULT'
  current_operator_id: string | null
  current_task_id: string | null
  engine_hours: number
  last_fuel_level_pct: number | null
  last_engine_temp_c: number | null
  last_health_score: number | null
  last_seen: string | null
  authorization_status: string
}

export interface MachineHealthComponent {
  score: number
  [key: string]: unknown
}

export interface MachineHealth {
  machine_id: string
  machine_code: string
  overall_health: number
  components: {
    engine: MachineHealthComponent
    fuel: MachineHealthComponent
    hydraulics: MachineHealthComponent
    electrical: MachineHealthComponent
    mechanical: MachineHealthComponent
    maintenance: MachineHealthComponent
  }
  active_faults: string[]
  maintenance_risk: 'LOW' | 'MEDIUM' | 'HIGH'
  computed_at: string
}

// ── Task ──────────────────────────────────────────────────────────────────────
export interface Task {
  task_id: string
  site_id: string
  zone_id: string | null
  machine_id: string | null
  operator_id: string | null
  task_type: string
  description: string | null
  material_type: string | null
  target_quantity: number | null
  completed_quantity: number
  unit: string | null
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'DELAYED' | 'PAUSED' | 'CANCELLED'
  scheduled_start: string | null
  actual_start: string | null
  actual_end: string | null
  estimated_duration_minutes: number | null
  actual_duration_minutes: number | null
  predicted_duration_minutes: number | null
  weather_condition: string | null
  terrain_type: string | null
  delay_reason: string | null
  priority: number
}

// ── Alert ─────────────────────────────────────────────────────────────────────
export interface Alert {
  alert_id: string
  timestamp: string
  site_id: string | null
  zone_id: string | null
  machine_id: string | null
  operator_id: string | null
  task_id: string | null
  alert_type: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  trigger_data: Record<string, unknown> | null
  message: string
  recommended_action: string | null
  acknowledged: boolean
  acknowledged_by: string | null
  acknowledged_at: string | null
  resolved: boolean
  resolved_at: string | null
}

// ── Incident ──────────────────────────────────────────────────────────────────
export interface Incident {
  incident_id: string
  timestamp: string
  site_id: string | null
  zone_id: string | null
  machine_id: string | null
  operator_id: string | null
  category: string
  severity: string
  description: string
  status: 'OPEN' | 'INVESTIGATING' | 'RESOLVED'
  assigned_to: string | null
  resolution: string | null
  is_auto_created: boolean
}

// ── KPI ───────────────────────────────────────────────────────────────────────
export interface SiteKPI {
  machines_active: number
  machines_total: number
  operators_active: number
  operators_total: number
  safety_score: number
  machine_health: number
  productivity: number
  active_alerts: number
  incidents_today: number
  as_of: string
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
export interface WsMessage {
  type: string
  payload: Record<string, unknown>
}

// ── API Response ──────────────────────────────────────────────────────────────
export interface ApiResponse<T> {
  data: T
  meta: {
    timestamp: string
    total?: number
    page?: number
    page_size?: number
  }
}

// ── Prestart ──────────────────────────────────────────────────────────────────
export interface PrestartItem {
  item_id: string
  label: string
  required: boolean
  passed: boolean
  blocked_reason: string | null
  auto_checked: boolean
}

export interface PrestartResult {
  authorization_status: 'AUTHORIZED' | 'BLOCKED' | 'REVIEW'
  blocked_reasons: string[]
  review_reasons: string[]
  check_id: string
  items: PrestartItem[]
  performed_at: string
}

// ── ETA ───────────────────────────────────────────────────────────────────────
export interface ETAPrediction {
  predicted_minutes: number
  confidence_interval: [number, number]
  mock: boolean
  message?: string
}

// ── Anomaly ───────────────────────────────────────────────────────────────────
export interface AnomalyResult {
  score: number
  label: 'NORMAL' | 'UNUSUAL'
  reason: string
  mock?: boolean
}
