import { useQuery } from '@tanstack/react-query'
import { BarChart3 } from 'lucide-react'
import { analyticsApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts'

export default function AnalyticsPage() {
  const { data: productivity } = useQuery({
    queryKey: ['productivity'],
    queryFn: () => analyticsApi.productivity(),
  })

  const prod = productivity as Record<string, unknown> | undefined

  const performanceData = [
    { metric: 'Completion', value: prod?.completion_rate_pct ?? 79 },
    { metric: 'ETA Accuracy', value: prod?.eta_accuracy_pct ?? 84 },
    { metric: 'Safety Score', value: 91 },
    { metric: 'Machine Health', value: 94 },
    { metric: 'Utilization', value: 87 },
  ]

  const radarData = [
    { subject: 'Safety', A: 91, fullMark: 100 },
    { subject: 'Health', A: 94, fullMark: 100 },
    { subject: 'Productivity', A: 79, fullMark: 100 },
    { subject: 'ETA', A: 84, fullMark: 100 },
    { subject: 'Idle', A: 72, fullMark: 100 },
    { subject: 'Training', A: 88, fullMark: 100 },
  ]

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Analytics" subtitle="Productivity, efficiency, and operational intelligence" icon={<BarChart3 size={20} />} />
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* KPI summary */}
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { label: 'Tasks Total', value: prod?.tasks_total ?? '—' },
            { label: 'Tasks Completed', value: prod?.tasks_completed ?? '—' },
            { label: 'Completion Rate', value: `${(prod?.completion_rate_pct as number)?.toFixed(1) ?? '—'}%` },
            { label: 'Avg Duration', value: `${(prod?.avg_actual_duration_minutes as number)?.toFixed(0) ?? '—'} min` },
            { label: 'ETA Accuracy', value: `${(prod?.eta_accuracy_pct as number)?.toFixed(1) ?? '—'}%` },
            { label: 'Material Moved', value: `${(prod?.material_moved_m3 as number)?.toFixed(0) ?? '—'} m³` },
          ].map(({ label, value }) => (
            <div key={label} className="card text-center">
              <div className="text-xl font-bold text-amber-400">{String(value)}</div>
              <div className="text-xs text-slate-500 mt-0.5">{label}</div>
            </div>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Performance Metrics</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={performanceData} margin={{ top: 0, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="metric" tick={{ fill: '#64748b', fontSize: 10 }} />
                <YAxis domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} />
                <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8 }} />
                <Bar dataKey="value" fill="#f59e0b" radius={[3, 3, 0, 0]} name="Score %" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Operational Radar</h3>
            <ResponsiveContainer width="100%" height={200}>
              <RadarChart data={radarData}>
                <PolarGrid stroke="#334155" />
                <PolarAngleAxis dataKey="subject" tick={{ fill: '#64748b', fontSize: 10 }} />
                <Radar name="Site" dataKey="A" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.2} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  )
}
