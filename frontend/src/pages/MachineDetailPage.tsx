import { useParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Activity, ChevronDown, ChevronUp, MessageSquare, AlertTriangle } from 'lucide-react'
import { useState } from 'react'
import { machinesApi, machineExtrasApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'
import StatusDot from '../components/ui/StatusDot'
import ExplainThis from '../components/ui/ExplainThis'
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

  const { data: machineSpeaksData } = useQuery({
    queryKey: ['machine-speaks', id],
    queryFn: () => machineExtrasApi.machineSpeaks(id!),
    enabled: !!id,
    refetchInterval: 30_000,
  })

  const { data: silentRiskData } = useQuery({
    queryKey: ['silent-risk', id],
    queryFn: () => machineExtrasApi.silentRisk(id!),
    enabled: !!id,
    refetchInterval: 30_000,
  })

  const machineSpeaks = machineSpeaksData as Record<string, unknown> | undefined
  const silentRisk = silentRiskData as Record<string, unknown> | undefined

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
        { label: 'RPM', value: String((health.components.engine as Record<string, unknown>)?.rpm ?? '—') + ' RPM' },
        { label: 'Temperature', value: String((health.components.engine as Record<string, unknown>)?.temperature_c ?? '—') + '°C' },
        { label: 'Oil Pressure', value: String((health.components.engine as Record<string, unknown>)?.oil_pressure_psi ?? '—') + ' PSI' },
        { label: 'Hours', value: String((health.components.engine as Record<string, unknown>)?.hours ?? '—') + ' h' },
        { label: 'Faults', value: health.active_faults.length > 0 ? health.active_faults.join(', ') : 'None' },
      ] : [],
    },
    {
      id: 'fuel', label: 'Fuel', score: health?.components.fuel?.score,
      fields: health ? [
        { label: 'Level', value: String((health.components.fuel as Record<string, unknown>)?.level_pct ?? '—') + '%' },
        { label: 'Consumption Rate', value: String((health.components.fuel as Record<string, unknown>)?.consumption_rate_lph ?? '—') + ' L/h' },
        { label: 'Efficiency Score', value: String((health.components.fuel as Record<string, unknown>)?.efficiency_score ?? '—') + '%' },
      ] : [],
    },
    {
      id: 'hydraulics', label: 'Hydraulics', score: health?.components.hydraulics?.score,
      fields: health ? [
        { label: 'Pressure', value: String((health.components.hydraulics as Record<string, unknown>)?.pressure_bar ?? '—') + ' bar' },
        { label: 'Temperature', value: String((health.components.hydraulics as Record<string, unknown>)?.temperature_c ?? '—') + '°C' },
        { label: 'Flow', value: String((health.components.hydraulics as Record<string, unknown>)?.flow_lpm ?? '—') + ' L/min' },
      ] : [],
    },
    {
      id: 'electrical', label: 'Electrical', score: health?.components.electrical?.score,
      fields: health ? [
        { label: 'Battery Voltage', value: String((health.components.electrical as Record<string, unknown>)?.battery_voltage ?? '—') + ' V' },
      ] : [],
    },
    {
      id: 'mechanical', label: 'Mechanical', score: health?.components.mechanical?.score,
      fields: health ? [
        { label: 'Vibration', value: String((health.components.mechanical as Record<string, unknown>)?.vibration_g ?? '—') + ' g' },
        { label: 'Brake Status', value: String((health.components.mechanical as Record<string, unknown>)?.brake_status ?? '—') },
        { label: 'Track/Tire Condition', value: String((health.components.mechanical as Record<string, unknown>)?.track_condition ?? '—') },
      ] : [],
    },
    {
      id: 'maintenance', label: 'Maintenance', score: health?.components.maintenance?.score,
      fields: health ? [
        { label: 'Last Service', value: (health.components.maintenance as Record<string, unknown>)?.last_service_days_ago != null ? `${(health.components.maintenance as Record<string, unknown>).last_service_days_ago} days ago` : '—' },
        { label: 'Next Service', value: (health.components.maintenance as Record<string, unknown>)?.next_service_due_hours != null ? `In ${(health.components.maintenance as Record<string, unknown>).next_service_due_hours} hours` : '—' },
        { label: 'Status', value: String((health.components.maintenance as Record<string, unknown>)?.status ?? '—') },
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
              <div className="flex items-center gap-1">
                <span className={`text-2xl font-bold ${health.overall_health >= 90 ? 'text-green-400' : health.overall_health >= 75 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {health.overall_health.toFixed(0)}%
                </span>
                <ExplainThis
                  title="Machine Health Score"
                  summary="Weighted composite of 6 subsystem scores. Computed from live telemetry and maintenance records."
                  components={[
                    { label: 'Engine', score: health.components.engine?.score, weight: 0.30, detail: 'RPM, temperature, oil pressure, fault codes' },
                    { label: 'Hydraulics', score: health.components.hydraulics?.score, weight: 0.20, detail: 'Pressure, temperature, flow rate' },
                    { label: 'Fuel System', score: health.components.fuel?.score, weight: 0.15, detail: 'Fuel level, consumption efficiency' },
                    { label: 'Mechanical', score: health.components.mechanical?.score, weight: 0.15, detail: 'Vibration, brake, track condition' },
                    { label: 'Electrical', score: health.components.electrical?.score, weight: 0.10, detail: 'Battery voltage, alternator' },
                    { label: 'Maintenance', score: health.components.maintenance?.score, weight: 0.10, detail: 'Days since service, service overdue risk' },
                  ]}
                  position="left"
                />
              </div>
            )}
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {/* Machine Speaks card */}
        {machineSpeaks && (
          <div className={`card border-l-4 ${
            machineSpeaks.tone === 'critical' ? 'border-red-500 bg-red-900/10' :
            machineSpeaks.tone === 'warning'  ? 'border-amber-500 bg-amber-900/10' :
            'border-green-500 bg-green-900/10'
          }`}>
            <div className="flex items-start gap-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                machineSpeaks.tone === 'critical' ? 'bg-red-500/20' :
                machineSpeaks.tone === 'warning' ? 'bg-amber-500/20' : 'bg-green-500/20'
              }`}>
                <MessageSquare size={14} className={
                  machineSpeaks.tone === 'critical' ? 'text-red-400' :
                  machineSpeaks.tone === 'warning' ? 'text-amber-400' : 'text-green-400'
                } />
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1 font-medium uppercase tracking-wide">
                  {machine.machine_code} — Machine Status
                </div>
                <p className="text-sm text-slate-200 leading-relaxed">"{machineSpeaks.message as string}"</p>
                <p className="text-xs text-slate-500 mt-1">Updated every 30 seconds</p>
              </div>
            </div>
          </div>
        )}

        {/* Silent Risk Detection */}
        {silentRisk && (silentRisk.risk_level as string) !== 'NONE' && (
          <div className={`card border ${
            (silentRisk.risk_level as string) === 'HIGH' ? 'border-red-700/50 bg-red-900/10' :
            (silentRisk.risk_level as string) === 'MEDIUM' ? 'border-amber-700/50 bg-amber-900/10' :
            'border-yellow-800/30'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle size={14} className={
                (silentRisk.risk_level as string) === 'HIGH' ? 'text-red-400' : 'text-amber-400'
              } />
              <span className="text-sm font-semibold text-slate-300">Composite Risk Detected</span>
              <span className={`text-xs px-2 py-0.5 rounded font-bold ${
                (silentRisk.risk_level as string) === 'HIGH' ? 'bg-red-900/40 text-red-400' :
                'bg-amber-900/40 text-amber-400'
              }`}>{silentRisk.risk_level as string}</span>
            </div>
            <p className="text-xs text-slate-300 mb-2">{silentRisk.message as string}</p>
            {((silentRisk.patterns as unknown[]) ?? []).map((p: unknown, i: number) => {
              const pattern = p as Record<string, unknown>
              return (
                <div key={i} className="text-xs bg-slate-700/30 rounded p-2 mb-1">
                  <span className="text-amber-300 font-medium">{pattern.label as string}</span>
                  <span className="text-slate-400 ml-2">— {pattern.description as string}</span>
                </div>
              )
            })}
          </div>
        )}

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
