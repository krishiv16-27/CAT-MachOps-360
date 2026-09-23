import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Truck, Users, Shield, Activity, BarChart3, Bell, AlertTriangle, RefreshCw,
} from 'lucide-react'
import { useKpiStore } from '../store/kpiStore'
import { useAlertStore } from '../store/alertStore'
import { analyticsApi, machinesApi, operatorsApi, alertsApi } from '../services/api'
import KpiCard from '../components/ui/KpiCard'
import Drawer from '../components/ui/Drawer'
import PageHeader from '../components/ui/PageHeader'
import SeverityBadge from '../components/ui/SeverityBadge'
import StatusDot from '../components/ui/StatusDot'
import { formatDistanceToNow } from 'date-fns'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Legend,
} from 'recharts'

type DrawerType = 'machines' | 'operators' | 'safety' | 'health' | 'productivity' | 'alerts' | 'incidents' | null

export default function DashboardPage() {
  const kpi = useKpiStore((s) => s.kpi)
  const { alerts: wsAlerts } = useAlertStore()
  const [drawer, setDrawer] = useState<DrawerType>(null)

  const { data: kpiData, isLoading: kpiLoading, refetch } = useQuery({
    queryKey: ['site-overview'],
    queryFn: () => analyticsApi.siteOverview(),
    refetchInterval: 30_000,
  })

  const { data: machinesData } = useQuery({
    queryKey: ['machines'],
    queryFn: () => machinesApi.list(),
    enabled: drawer === 'machines' || drawer === 'health',
  })

  const { data: operatorsData } = useQuery({
    queryKey: ['operators'],
    queryFn: () => operatorsApi.list(),
    enabled: drawer === 'operators',
  })

  const { data: alertsData } = useQuery({
    queryKey: ['alerts', 'unresolved'],
    queryFn: () => alertsApi.list({ resolved: 'false', page_size: '50' }),
    enabled: drawer === 'alerts',
  })

  const { data: productivityData } = useQuery({
    queryKey: ['analytics', 'productivity'],
    queryFn: () => analyticsApi.productivity(),
    enabled: drawer === 'productivity',
  })

  const d = kpi ?? kpiData

  // Mock sparkline data for charts
  const healthTrend = Array.from({ length: 12 }, (_, i) => ({
    h: `${i + 1}h`, health: 88 + Math.sin(i * 0.5) * 5, safety: 85 + Math.cos(i * 0.4) * 6,
  }))

  const taskTrend = Array.from({ length: 7 }, (_, i) => ({
    day: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i],
    completed: Math.floor(Math.random() * 8) + 10,
    delayed: Math.floor(Math.random() * 3),
  }))

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Command Center"
        subtitle="Site-wide operational intelligence"
        icon={<BarChart3 size={20} />}
        actions={
          <button
            onClick={() => refetch()}
            className="btn-secondary text-xs flex items-center gap-1.5"
            aria-label="Refresh dashboard data"
          >
            <RefreshCw size={12} />
            Refresh
          </button>
        }
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          <KpiCard
            title="Machines Active"
            value={d ? `${d.machines_active}/${d.machines_total}` : '—'}
            icon={<Truck size={18} />}
            severity={d && d.machines_active < d.machines_total * 0.5 ? 'warning' : 'success'}
            subtitle={`${d?.machines_total ?? 0} total`}
            onClick={() => setDrawer('machines')}
            loading={kpiLoading}
          />
          <KpiCard
            title="Operators Active"
            value={d ? `${d.operators_active}/${d.operators_total}` : '—'}
            icon={<Users size={18} />}
            severity="info"
            subtitle={`${d?.operators_total ?? 0} total`}
            onClick={() => setDrawer('operators')}
            loading={kpiLoading}
          />
          <KpiCard
            title="Safety Score"
            value={d ? `${d.safety_score}%` : '—'}
            icon={<Shield size={18} />}
            severity={d && d.safety_score >= 90 ? 'success' : d && d.safety_score >= 75 ? 'warning' : 'danger'}
            trend={d ? `${d.safety_score >= 90 ? '+' : ''}${(d.safety_score - 88).toFixed(1)}%` : undefined}
            trendDir={d && d.safety_score >= 90 ? 'up' : 'down'}
            onClick={() => setDrawer('safety')}
            loading={kpiLoading}
          />
          <KpiCard
            title="Machine Health"
            value={d ? `${d.machine_health}%` : '—'}
            icon={<Activity size={18} />}
            severity={d && d.machine_health >= 90 ? 'success' : d && d.machine_health >= 75 ? 'warning' : 'danger'}
            onClick={() => setDrawer('health')}
            loading={kpiLoading}
          />
          <KpiCard
            title="Productivity"
            value={d ? `${d.productivity}%` : '—'}
            icon={<BarChart3 size={18} />}
            severity={d && d.productivity >= 80 ? 'success' : 'warning'}
            onClick={() => setDrawer('productivity')}
            loading={kpiLoading}
          />
          <KpiCard
            title="Active Alerts"
            value={d?.active_alerts ?? wsAlerts.filter((a) => !a.resolved).length}
            icon={<Bell size={18} />}
            severity={d && d.active_alerts === 0 ? 'success' : d && d.active_alerts > 5 ? 'danger' : 'warning'}
            badge={wsAlerts.filter((a) => a.severity === 'CRITICAL' && !a.acknowledged).length > 0 ? 'CRITICAL' : undefined}
            onClick={() => setDrawer('alerts')}
            loading={kpiLoading}
          />
          <KpiCard
            title="Incidents Today"
            value={d?.incidents_today ?? 0}
            icon={<AlertTriangle size={18} />}
            severity={d && d.incidents_today === 0 ? 'success' : d && d.incidents_today > 3 ? 'danger' : 'warning'}
            onClick={() => setDrawer('incidents')}
            loading={kpiLoading}
          />
        </div>

        {/* Charts row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Health & Safety Trend (12h)</h3>
            <ResponsiveContainer width="100%" height={180}>
              <LineChart data={healthTrend} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="h" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis domain={[70, 100]} tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                  labelStyle={{ color: '#94a3b8' }}
                />
                <Line type="monotone" dataKey="health" stroke="#f59e0b" strokeWidth={2} dot={false} name="Health" />
                <Line type="monotone" dataKey="safety" stroke="#4ade80" strokeWidth={2} dot={false} name="Safety" />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Task Completion (7 days)</h3>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={taskTrend} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 11 }} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                />
                <Bar dataKey="completed" fill="#f59e0b" name="Completed" radius={[2, 2, 0, 0]} />
                <Bar dataKey="delayed" fill="#ef4444" name="Delayed" radius={[2, 2, 0, 0]} />
                <Legend wrapperStyle={{ fontSize: 11, color: '#64748b' }} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Live alerts feed */}
        <div className="card">
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Live Alert Feed</h3>
          {wsAlerts.length === 0 ? (
            <p className="text-sm text-slate-500 py-4 text-center">No active alerts</p>
          ) : (
            <div className="space-y-2">
              {wsAlerts.slice(0, 8).map((a) => (
                <div key={a.alert_id} className={`flex items-start gap-3 p-3 rounded-lg border ${
                  a.severity === 'CRITICAL' ? 'bg-red-900/20 border-red-800/50' :
                  a.severity === 'HIGH' ? 'bg-orange-900/20 border-orange-800/50' :
                  'bg-slate-700/30 border-slate-700'
                }`}>
                  <StatusDot
                    status={a.severity === 'CRITICAL' || a.severity === 'HIGH' ? 'red' : a.severity === 'MEDIUM' ? 'amber' : 'blue'}
                    pulse={!a.acknowledged}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <SeverityBadge severity={a.severity} />
                      <span className="text-xs text-slate-400">{a.alert_type.replace(/_/g, ' ')}</span>
                      {a.machine_id && <span className="text-xs text-slate-500">· {a.machine_id.slice(0, 8)}</span>}
                    </div>
                    <p className="text-xs text-slate-300 mt-0.5 truncate">{a.message}</p>
                  </div>
                  <div className="text-xs text-slate-500 flex-shrink-0">
                    {formatDistanceToNow(new Date(a.timestamp), { addSuffix: true })}
                  </div>
                  {a.acknowledged && (
                    <span className="text-xs text-green-400">✓ ACK</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── Drawers ──────────────────────────────────────────────────────────── */}

      {/* Machines drawer */}
      <Drawer isOpen={drawer === 'machines'} onClose={() => setDrawer(null)} title="Active Machines" width="xl">
        <MachinesDrawer machines={machinesData} />
      </Drawer>

      {/* Operators drawer */}
      <Drawer isOpen={drawer === 'operators'} onClose={() => setDrawer(null)} title="Active Operators" width="xl">
        <OperatorsDrawer operators={operatorsData} />
      </Drawer>

      {/* Safety score drawer */}
      <Drawer isOpen={drawer === 'safety'} onClose={() => setDrawer(null)} title="Safety Score Breakdown" subtitle="Operational Safety Score (Demo Index)">
        <SafetyDrawer safetyScore={d?.safety_score} />
      </Drawer>

      {/* Machine health drawer */}
      <Drawer isOpen={drawer === 'health'} onClose={() => setDrawer(null)} title="Fleet Health Overview" width="xl">
        <HealthDrawer machines={machinesData} />
      </Drawer>

      {/* Productivity drawer */}
      <Drawer isOpen={drawer === 'productivity'} onClose={() => setDrawer(null)} title="Productivity Analytics">
        <ProductivityDrawer data={productivityData as Record<string, unknown>} />
      </Drawer>

      {/* Alerts drawer */}
      <Drawer isOpen={drawer === 'alerts'} onClose={() => setDrawer(null)} title="Active Alerts" width="xl">
        <AlertsDrawer alerts={alertsData ?? wsAlerts} />
      </Drawer>

      {/* Incidents drawer */}
      <Drawer isOpen={drawer === 'incidents'} onClose={() => setDrawer(null)} title="Incidents Today">
        <div className="text-slate-400 text-sm">See the full Incidents page for details.</div>
      </Drawer>
    </div>
  )
}

// ── Drawer content components ─────────────────────────────────────────────────

function MachinesDrawer({ machines }: { machines?: import('../types').MachineSummary[] }) {
  if (!machines) return <div className="text-slate-400 text-sm animate-pulse">Loading machines…</div>
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-slate-500 border-b border-slate-700">
            <th className="pb-2 pr-3">Code</th>
            <th className="pb-2 pr-3">Type</th>
            <th className="pb-2 pr-3">Status</th>
            <th className="pb-2 pr-3">Operator</th>
            <th className="pb-2 pr-3">Health</th>
            <th className="pb-2 pr-3">Fuel</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/50">
          {machines.map((m) => (
            <tr key={m.machine_id} className="hover:bg-slate-700/20">
              <td className="py-2.5 pr-3 font-mono text-amber-400 font-medium">{m.machine_code}</td>
              <td className="py-2.5 pr-3 text-slate-300">{m.machine_type}</td>
              <td className="py-2.5 pr-3">
                <StatusDot
                  status={m.status === 'ACTIVE' ? 'green' : m.status === 'MAINTENANCE' ? 'amber' : 'gray'}
                  label={m.status}
                />
              </td>
              <td className="py-2.5 pr-3 text-slate-400">{m.current_operator_id?.slice(0, 8) ?? '—'}</td>
              <td className="py-2.5 pr-3">
                <span className={`font-medium ${m.last_health_score && m.last_health_score >= 90 ? 'text-green-400' : m.last_health_score && m.last_health_score >= 75 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {m.last_health_score?.toFixed(0) ?? '—'}%
                </span>
              </td>
              <td className="py-2.5 pr-3">
                <div className="flex items-center gap-2">
                  <div className="w-16 bg-slate-700 rounded-full h-1.5">
                    <div
                      className="h-1.5 rounded-full bg-amber-500"
                      style={{ width: `${m.last_fuel_level_pct ?? 0}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400">{m.last_fuel_level_pct?.toFixed(0) ?? 0}%</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function OperatorsDrawer({ operators }: { operators?: import('../types').OperatorSummary[] }) {
  if (!operators) return <div className="text-slate-400 text-sm animate-pulse">Loading operators…</div>
  return (
    <div className="space-y-3">
      {operators.map((op) => (
        <div key={op.operator_id} className="card flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-amber-500/20 rounded-full flex items-center justify-center text-amber-400 font-bold text-sm">
              {op.name[0]}
            </div>
            <div>
              <div className="font-medium text-slate-200 text-sm">{op.name}</div>
              <div className="text-xs text-slate-500">{op.employee_code} · {op.experience_years}yr exp · L{op.skill_level}</div>
            </div>
          </div>
          <div className="text-right">
            <StatusDot
              status={op.shift_status === 'ON_SHIFT' ? 'green' : op.shift_status === 'ON_BREAK' ? 'amber' : 'gray'}
              label={op.shift_status.replace('_', ' ')}
            />
            <div className="text-xs text-slate-500 mt-1">Safety: <span className="text-green-400">{op.safety_score?.toFixed(0)}%</span></div>
          </div>
        </div>
      ))}
    </div>
  )
}

function SafetyDrawer({ safetyScore }: { safetyScore?: number }) {
  const components = [
    { label: 'Seatbelt Compliance', score: 95, weight: 25, events: 1 },
    { label: 'Proximity Events', score: 82, weight: 20, events: 3 },
    { label: 'Speed Violations', score: 100, weight: 15, events: 0 },
    { label: 'Incident Rate', score: 90, weight: 20, incidents: 1 },
    { label: 'Pre-Start Compliance', score: 100, weight: 10 },
    { label: 'Training Completion', score: 78, weight: 10, pending: 2 },
  ]
  return (
    <div className="space-y-4">
      <div className="text-center py-4">
        <div className="text-5xl font-bold text-amber-400">{safetyScore?.toFixed(1) ?? '91.0'}%</div>
        <div className="text-sm text-slate-400 mt-1">Operational Safety Score (Demo Index)</div>
      </div>
      <div className="space-y-3">
        {components.map((c) => (
          <div key={c.label} className="card">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-slate-300">{c.label}</span>
              <span className={`text-sm font-bold ${c.score >= 90 ? 'text-green-400' : c.score >= 75 ? 'text-yellow-400' : 'text-red-400'}`}>
                {c.score}%
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div className={`h-2 rounded-full ${c.score >= 90 ? 'bg-green-500' : c.score >= 75 ? 'bg-yellow-500' : 'bg-red-500'}`}
                style={{ width: `${c.score}%` }} />
            </div>
            <div className="flex items-center justify-between mt-1">
              <span className="text-xs text-slate-500">Weight: {c.weight}%</span>
              {c.events !== undefined && <span className="text-xs text-slate-500">{c.events} events</span>}
              {c.incidents !== undefined && <span className="text-xs text-slate-500">{c.incidents} incidents</span>}
              {c.pending !== undefined && <span className="text-xs text-yellow-500">{c.pending} modules pending</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function HealthDrawer({ machines }: { machines?: import('../types').MachineSummary[] }) {
  if (!machines) return <div className="text-slate-400 text-sm">Loading…</div>
  return (
    <div className="space-y-3">
      {machines.slice(0, 7).map((m) => (
        <div key={m.machine_id} className="card">
          <div className="flex items-center justify-between mb-3">
            <span className="font-mono font-medium text-amber-400">{m.machine_code}</span>
            <span className={`text-lg font-bold ${m.last_health_score && m.last_health_score >= 90 ? 'text-green-400' : 'text-yellow-400'}`}>
              {m.last_health_score?.toFixed(0) ?? '?'}%
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs text-slate-400">
            <span>Fuel: <span className="text-slate-200">{m.last_fuel_level_pct?.toFixed(0) ?? '?'}%</span></span>
            <span>Temp: <span className="text-slate-200">{m.last_engine_temp_c?.toFixed(0) ?? '?'}°C</span></span>
            <span>Hours: <span className="text-slate-200">{m.engine_hours.toFixed(0)}h</span></span>
          </div>
        </div>
      ))}
    </div>
  )
}

function ProductivityDrawer({ data }: { data?: Record<string, unknown> }) {
  const stats = data ?? {
    tasks_total: 24,
    tasks_completed: 19,
    completion_rate_pct: 79.2,
    avg_actual_duration_minutes: 68.4,
    eta_accuracy_pct: 84.1,
    material_moved_m3: 4820,
  }
  return (
    <div className="space-y-4">
      {Object.entries(stats).map(([k, v]) => (
        <div key={k} className="flex justify-between items-center p-3 bg-slate-700/30 rounded-lg">
          <span className="text-sm text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
          <span className="text-sm font-semibold text-slate-100">{typeof v === 'number' ? v.toFixed(1) : String(v)}</span>
        </div>
      ))}
    </div>
  )
}

function AlertsDrawer({ alerts }: { alerts: import('../types').Alert[] }) {
  return (
    <div className="space-y-3">
      {alerts.length === 0 && <p className="text-slate-500 text-sm text-center py-8">No active alerts</p>}
      {alerts.map((a) => (
        <div key={a.alert_id} className={`p-4 rounded-lg border ${
          a.severity === 'CRITICAL' ? 'bg-red-900/20 border-red-800/50' :
          a.severity === 'HIGH' ? 'bg-orange-900/20 border-orange-800/50' :
          'bg-slate-700/30 border-slate-700'
        }`}>
          <div className="flex items-center gap-2 mb-2">
            <SeverityBadge severity={a.severity} />
            <span className="text-xs text-slate-400">{a.alert_type.replace(/_/g, ' ')}</span>
          </div>
          <p className="text-sm text-slate-300">{a.message}</p>
          {a.recommended_action && (
            <p className="text-xs text-slate-500 mt-1">→ {a.recommended_action}</p>
          )}
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
            <span>{new Date(a.timestamp).toLocaleTimeString()}</span>
            {a.acknowledged && <span className="text-green-400">✓ Acknowledged</span>}
            {!a.acknowledged && <span className="text-yellow-400">⚠ Unacknowledged</span>}
          </div>
        </div>
      ))}
    </div>
  )
}
