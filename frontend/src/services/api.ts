/**
 * API service functions.
 * All calls go through the Vite proxy to http://localhost:8000.
 */
import { useAuthStore } from '../store/authStore'

const BASE = '/api/v1'

function getToken(): string {
  return useAuthStore.getState().token ?? ''
}

function authHeaders(): HeadersInit {
  const token = getToken()
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: authHeaders(),
    body: body ? JSON.stringify(body) : undefined,
  })
  const json = await res.json()
  if (!res.ok) {
    throw new Error(json?.error?.message ?? `Request failed: ${res.status}`)
  }
  return json.data as T
}

const get = <T>(path: string) => request<T>('GET', path)
const post = <T>(path: string, body: unknown) => request<T>('POST', path, body)
const patch = <T>(path: string, body: unknown) => request<T>('PATCH', path, body)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    post<{ access_token: string; user: import('../types').User }>('/auth/login', { email, password }),
  me: () => get<import('../types').User>('/auth/me'),
}

// ── KPI ───────────────────────────────────────────────────────────────────────
export const analyticsApi = {
  siteOverview: () => get<import('../types').SiteKPI>('/analytics/site-overview'),
  productivity: (siteId?: string) =>
    get<Record<string, unknown>>(`/analytics/productivity${siteId ? `?site_id=${siteId}` : ''}`),
}

// ── Machines ──────────────────────────────────────────────────────────────────
export const machinesApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return get<import('../types').MachineSummary[]>(`/machines${q}`)
  },
  get: (id: string) => get<import('../types').MachineSummary>(`/machines/${id}`),
  health: (id: string) => get<import('../types').MachineHealth>(`/machines/${id}/health`),
  telemetry: (id: string, limit = 50) =>
    get<Record<string, unknown>[]>(`/machines/${id}/telemetry?limit=${limit}`),
}

// ── Operators ─────────────────────────────────────────────────────────────────
export const operatorsApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return get<import('../types').OperatorSummary[]>(`/operators${q}`)
  },
  get: (id: string) => get<import('../types').OperatorSummary>(`/operators/${id}`),
  safetyScore: (id: string) => get<Record<string, unknown>>(`/operators/${id}/safety-score`),
  timeline: (id: string, date?: string) =>
    get<{ entries: import('../types').TimelineEntry[]; totals: Record<string, number> }>(
      `/operators/${id}/timeline${date ? `?date=${date}` : ''}`
    ),
  recommendations: (id: string) =>
    get<Record<string, unknown>[]>(`/operators/${id}/training-recommendations`),
}

// ── Tasks ─────────────────────────────────────────────────────────────────────
export const tasksApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return get<import('../types').Task[]>(`/tasks${q}`)
  },
  get: (id: string) => get<import('../types').Task>(`/tasks/${id}`),
  start: (id: string) => post<Record<string, unknown>>(`/tasks/${id}/start`, {}),
  complete: (id: string) => post<Record<string, unknown>>(`/tasks/${id}/complete`, {}),
}

// ── Alerts ────────────────────────────────────────────────────────────────────
export const alertsApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return get<import('../types').Alert[]>(`/alerts${q}`)
  },
  get: (id: string) => get<import('../types').Alert>(`/alerts/${id}`),
  acknowledge: (id: string, note?: string) =>
    post<Record<string, unknown>>(`/alerts/${id}/acknowledge`, { note }),
}

// ── Incidents ─────────────────────────────────────────────────────────────────
export const incidentsApi = {
  list: (params?: Record<string, string>) => {
    const q = params ? '?' + new URLSearchParams(params).toString() : ''
    return get<import('../types').Incident[]>(`/incidents${q}`)
  },
  get: (id: string) => get<import('../types').Incident>(`/incidents/${id}`),
  create: (body: Record<string, unknown>) =>
    post<import('../types').Incident>('/incidents', body),
}

// ── Pre-start ─────────────────────────────────────────────────────────────────
export const prestartApi = {
  getChecklist: (machineId: string, operatorId: string) =>
    get<Record<string, unknown>>(`/prestart/checklist?machine_id=${machineId}&operator_id=${operatorId}`),
  submit: (body: Record<string, unknown>) =>
    post<import('../types').PrestartResult>('/prestart/submit', body),
}

// ── ML ────────────────────────────────────────────────────────────────────────
export const mlApi = {
  predictEta: (features: Record<string, unknown>) =>
    post<import('../types').ETAPrediction>('/ml/predict-eta', features),
  anomalyCheck: (operatorId: string) =>
    post<import('../types').AnomalyResult>('/ml/anomaly-check', { operator_id: operatorId }),
}

// ── Simulator ─────────────────────────────────────────────────────────────────
export const simulatorApi = {
  activate: (scenario: string, machineId?: string, operatorId?: string) =>
    post<Record<string, unknown>>('/simulator/activate', {
      scenario,
      machine_id: machineId,
      operator_id: operatorId,
    }),
  reset: () => post<Record<string, unknown>>('/simulator/reset', {}),
  status: () => get<Record<string, unknown>>('/simulator/status'),
}

// ── CV ────────────────────────────────────────────────────────────────────────
export const cvApi = {
  events: () => get<Record<string, unknown>[]>('/cv/events'),
  cameras: () => get<Record<string, unknown>[]>('/cv/cameras'),
  simulate: (eventType: string, machineId: string, distanceM?: number) =>
    post<Record<string, unknown>>('/cv/simulate', { event_type: eventType, machine_id: machineId, distance_m: distanceM }),
}

// ── Training ──────────────────────────────────────────────────────────────────
export const trainingApi = {
  modules: () => get<Record<string, unknown>[]>('/training/modules'),
  operatorStatus: (id: string) => get<Record<string, unknown>[]>(`/training/operator/${id}`),
}

// ── Copilot ───────────────────────────────────────────────────────────────────
export const copilotApi = {
  query: (question: string, contextFilter?: Record<string, unknown>) =>
    post<{ answer: string; sources: Record<string, unknown>[]; disclaimer: string; mock: boolean }>(
      '/copilot/query', { question, context_filter: contextFilter }
    ),
  history: () => get<Record<string, unknown>[]>('/copilot/history'),
  clearHistory: () => request<Record<string, unknown>>('DELETE', '/copilot/history'),
}

// ── New Phase C/D endpoints ───────────────────────────────────────────────────
export const operatorExtrasApi = {
  shiftNarrative: (id: string) =>
    get<Record<string, unknown>>(`/operators/${id}/shift-narrative`),
  carbonPassport: (id: string) =>
    get<Record<string, unknown>>(`/operators/${id}/carbon-passport`),
  nearMisses: (id: string, days = 7) =>
    get<Record<string, unknown>>(`/operators/${id}/near-misses?days=${days}`),
  gutCheckToday: (id: string) =>
    get<Record<string, unknown>>(`/operators/${id}/gut-check/today`),
  submitGutCheck: (id: string, body: Record<string, boolean | null>) =>
    post<Record<string, unknown>>(`/operators/${id}/gut-check`, body),
}

export const machineExtrasApi = {
  silentRisk: (id: string) =>
    get<Record<string, unknown>>(`/machines/${id}/silent-risk`),
  machineSpeaks: (id: string) =>
    get<Record<string, unknown>>(`/machines/${id}/machine-speaks`),
}

export const compatibilityApi = {
  score: (operatorId: string, machineId: string, taskType?: string) =>
    get<Record<string, unknown>>(
      `/compatibility?operator_id=${operatorId}&machine_id=${machineId}${taskType ? `&task_type=${taskType}` : ''}`
    ),
}

export const sitemapApi = {
  get: () => get<Record<string, unknown>>('/sitemap'),
  simulateApproach: () => post<Record<string, unknown>>('/sitemap/simulate-approach', {}),
}
