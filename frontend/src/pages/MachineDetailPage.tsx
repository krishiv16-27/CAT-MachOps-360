import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Activity, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { machinesApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'
import StatusDot from '../components/ui/StatusDot'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function MachineDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [expandedSection, setExpandedSection] = useState<string | null>('engine')

  const { data: machine } = useQuery({
    queryKey: ['machine', id],
    queryFn: () => machinesApi.get(id!),
    enabled: !!id,
  })

  const { data: health } = useQuery({
    queryKey: ['machine-health', id],
    queryFn: () => machinesApi.health(id!),
    enabled: !!id,
    refetchInterval: 30_000,
  })

  const { data: telemetry } = useQuery({
    queryKey: ['machine-telemetry', id],
    queryFn: () => machinesApi.telemetry(id!, 30),
    enabled: !!id,
    refetchInterval: 15_000,
  })

  const telemetryChartData = (telemetry ?? []).slice().reverse().map((t, i) => ({
    t: i,
    rpm: t.engine_rpm,
    temp: t.engine_temperature_c,
    load: t.machine_load_pct,
    fuel: t.fuel_level_pct,
  }))

  if (!machine) return <div className="p-6 text-slate-400">Loading…</div>

  const sections = [
    {
      id: 'engine', label: 'Engine', score: health?.components.engine?.score,
      fields: health ? [
        { label: 'Status', value: machine.status },
        { label: 'RPM', value: health.components.engine?.rpm?.toFixed(0) + ' RPM' },
        { label: 'Temperature', value: health.components.engine?.temperature_c?.toFixed(0) + '°C' },
        { label: 'Oil Pressure', value: health.components.engine?.oil_pressure_psi?.toFixed(0) + ' PSI' },
        { label: 'Hours', value: health.components.engine?.hours?.toFixed(0) + ' h' },
        { label: 'Faults', value: health.active_faults.length > 0 ? health.active_faults.join(', ') : 'None' },
      ] : [],
    },
    {
      id: 'fuel', label: 'Fuel', score: health?.components.fuel?.score,
      fields: health ? [
        { label: 'Level', value: health.components.fuel?.level_pct?.toFixed(0) + '%' },
        { label: 'Consumption Rate', value: health.components.fuel?.consumption_rate_lph?.toFixed(1) + ' L/h' },
        { label: 'Efficiency Score', value: health.components.fuel?.efficiency_score?.toFixed(0) + '%' },
      ] : [],
    },
    {
      id: 'hydraulics', label: 'Hydraulics', score: health?.components.hydraulics?.score,
      fields: health ? [
        { label: 'Pressure', value: health.components.hydraulics?.pressure_bar?.toFixed(0) + ' bar' },
        { label: 'Temperature', value: health.components.hydraulics?.temperature_c?.toFixed(0) + '°C' },
        { label: 'Flow', value: health.components.hydraulics?.flow_lpm?.toFixed(0) + ' L/min' },
      ] : [],
    },
    {
      id: 'electrical', label: 'Electrical', score: health?.components.electrical?.score,
      fields: health ? [
        { label: 'Battery Voltage', value: health.components.electrical?.battery_voltage?.toFixed(1) + ' V' },
      ] : [],
    },
    {
      id: 'mechanical', label: 'Mechanical', score: health?.components.mechanical?.score,
      fields: health ? [
        { label: 'Vibration', value: health.components.mechanical?.vibration_g?.toFixed(2) + ' g' },
        { label: 'Brake Status', value: String(health.components.mechanical?.brake_status) },
        { label: 'Track/Tire Condition', value: String(health.components.mechanical?.track_condition) },
      ] : [],
    },
    {
      id: 'maintenance', label: 'Maintenance', score: health?.components.maintenance?.score,
      fields: health ? [
        { label: 'Last Service', value: health.components.maintenance?.last_service_days_ago != null ? `${health.components.maintenance.last_service_days_ago} days ago` : '—' },
        { label: 'Next Service', value: health.components.maintenance?.next_service_due_hours != null ? `In ${health.components.maintenance.next_service_due_hours?.toFixed(0)} hours` : '—' },
        { label: 'Status', value: String(health.components.maintenance?.status) },
        { label: 'Maintenance Risk', value: health.maintenance_risk },
      ] : [],
    },
  ]

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title={machine.machine_code}
        subtitle={`${machine.machine_type} — ${machine.model_name}`}
        icon={<Activity size={20} />}
        actions={
          <div className="flex items-center gap-3">
            <StatusDot
              status={machine.status === 'ACTIVE' ? 'green' : machine.status === 'MAINTENANCE' ? 'amber' : 'gray'}
              pulse={machine.status === 'ACTIVE'}
              label={machine.status}
            />
            {health && (
              <span className={`text-2xl font-bold ${health.overall_health >= 90 ? 'text-green-400' : health.overall_health >= 75 ? 'text-yellow-400' : 'text-red-400'}`}>
                {health.overall_health.toFixed(0)}%
              </span>
            )}
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {/* Telemetry chart */}
        {telemetryChartData.length > 0 && (
          <div className="card">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Live Telemetry (last 30 readings)</h3>
            <ResponsiveContainer width="100%" height={160}>
              <LineChart data={telemetryChartData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="t" tick={false} />
                <YAxis tick={{ fill: '#64748b', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                <Line type="monotone" dataKey="rpm" stroke="#f59e0b" strokeWidth={1.5} dot={false} name="RPM" />
                <Line type="monotone" dataKey="temp" stroke="#ef4444" strokeWidth={1.5} dot={false} name="Temp°C" />
                <Line type="monotone" dataKey="load" stroke="#4ade80" strokeWidth={1.5} dot={false} name="Load%" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Health sections */}
        {sections.map((section) => (
          <div key={section.id} className="card">
            <button
              className="w-full flex items-center justify-between"
              onClick={() => setExpandedSection(expandedSection === section.id ? null : section.id)}
              aria-expanded={expandedSection === section.id}
              aria-label={`${section.label} health section`}
            >
              <div className="flex items-center gap-3">
                <span className="font-medium text-slate-200">{section.label}</span>
                {section.score != null && (
                  <span className={`text-sm font-bold ${section.score >= 90 ? 'text-green-400' : section.score >= 75 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {(section.score as number).toFixed(0)}%
                  </span>
                )}
              </div>
              {expandedSection === section.id ? <ChevronUp size={16} className="text-slate-500" /> : <ChevronDown size={16} className="text-slate-500" />}
            </button>
            {expandedSection === section.id && section.fields.length > 0 && (
              <div className="mt-4 grid grid-cols-2 gap-3">
                {section.fields.map((f) => (
                  <div key={f.label} className="bg-slate-700/30 rounded-lg p-3">
                    <div className="text-xs text-slate-500 mb-0.5">{f.label}</div>
                    <div className="text-sm font-medium text-slate-200">{f.value}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
