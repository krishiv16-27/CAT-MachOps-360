import { useQuery } from '@tanstack/react-query'
import { ClipboardList } from 'lucide-react'
import { tasksApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'
import StatusDot from '../components/ui/StatusDot'
import { format } from 'date-fns'

export default function TasksPage() {
  const { data: tasks, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list({ page_size: '50' }),
    refetchInterval: 15_000,
  })

  const statusColor: Record<string, 'green' | 'amber' | 'red' | 'blue' | 'gray'> = {
    COMPLETED: 'green', IN_PROGRESS: 'amber', PENDING: 'blue', DELAYED: 'red', CANCELLED: 'gray', PAUSED: 'gray',
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Tasks" subtitle="Site-wide task management and ETA tracking" icon={<ClipboardList size={20} />} />
      <div className="p-6">
        {isLoading && <div className="text-slate-400 text-sm animate-pulse">Loading tasks…</div>}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-slate-500 border-b border-slate-700">
                {['Type', 'Status', 'Machine', 'Operator', 'Progress', 'Est. Duration', 'Actual / ETA', 'Start', 'Weather'].map((h) => (
                  <th key={h} className="pb-3 pr-4 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {tasks?.map((t) => {
                const progress = t.target_quantity ? (t.completed_quantity / t.target_quantity) * 100 : 0
                return (
                  <tr key={t.task_id} className="hover:bg-slate-700/20">
                    <td className="py-3 pr-4 font-medium text-slate-200">{t.task_type}</td>
                    <td className="py-3 pr-4">
                      <StatusDot status={statusColor[t.status] ?? 'gray'} label={t.status} />
                    </td>
                    <td className="py-3 pr-4 font-mono text-amber-400 text-xs">{t.machine_id?.slice(0, 8) ?? '—'}</td>
                    <td className="py-3 pr-4 text-slate-400 text-xs">{t.operator_id?.slice(0, 8) ?? '—'}</td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-700 rounded-full h-1.5">
                          <div className="h-1.5 rounded-full bg-amber-500" style={{ width: `${Math.min(progress, 100)}%` }} />
                        </div>
                        <span className="text-xs text-slate-400">{progress.toFixed(0)}%</span>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-slate-400">{t.estimated_duration_minutes?.toFixed(0) ?? '—'} min</td>
                    <td className="py-3 pr-4 text-slate-400">
                      {t.actual_duration_minutes?.toFixed(0) ?? t.predicted_duration_minutes?.toFixed(0) ?? '—'} min
                      {t.predicted_duration_minutes && !t.actual_duration_minutes && <span className="text-xs text-amber-400 ml-1">(ML)</span>}
                    </td>
                    <td className="py-3 pr-4 text-slate-500 text-xs">
                      {t.actual_start ? format(new Date(t.actual_start), 'HH:mm') : '—'}
                    </td>
                    <td className="py-3 pr-4 text-slate-500 text-xs">{t.weather_condition ?? '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
