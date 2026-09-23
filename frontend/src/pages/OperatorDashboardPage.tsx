import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '../store/authStore'
import { tasksApi, operatorsApi, alertsApi, prestartApi, machinesApi } from '../services/api'
import { useAlertStore } from '../store/alertStore'
import { Link } from 'react-router-dom'
import { Watch, ShieldCheck, Bell, ClipboardList, BookOpen, AlertTriangle } from 'lucide-react'
import StatusDot from '../components/ui/StatusDot'
import SeverityBadge from '../components/ui/SeverityBadge'
import { formatDistanceToNow } from 'date-fns'

export default function OperatorDashboardPage() {
  const { user } = useAuthStore()
  const { alerts: wsAlerts } = useAlertStore()
  const operatorId = user?.operator_id

  const { data: operator } = useQuery({
    queryKey: ['operator', operatorId],
    queryFn: () => operatorsApi.get(operatorId!),
    enabled: !!operatorId,
    refetchInterval: 30_000,
  })

  const { data: tasks } = useQuery({
    queryKey: ['tasks', operatorId],
    queryFn: () => tasksApi.list({ operator_id: operatorId!, page_size: '10' }),
    enabled: !!operatorId,
    refetchInterval: 15_000,
  })

  const { data: myAlerts } = useQuery({
    queryKey: ['alerts', operatorId],
    queryFn: () => alertsApi.list({ operator_id: operatorId!, resolved: 'false', page_size: '5' }),
    enabled: !!operatorId,
    refetchInterval: 10_000,
  })

  const currentTask = tasks?.find((t) => t.status === 'IN_PROGRESS')
  const nextTask = tasks?.find((t) => t.status === 'PENDING')
  const completedToday = tasks?.filter((t) => t.status === 'COMPLETED').length ?? 0
  const allAlerts = myAlerts ?? wsAlerts

  return (
    <div className="flex flex-col h-full bg-slate-900">
      {/* Header */}
      <div className="px-6 py-5 border-b border-slate-700/50 bg-slate-800/30">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-100">
              Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'}, {operator?.name?.split(' ')[0] ?? user?.name?.split(' ')[0]}
            </h1>
            <p className="text-sm text-slate-400 mt-0.5">
              {operator?.employee_code ?? ''} · Level {operator?.skill_level} · {operator?.experience_years}yr exp
            </p>
          </div>
          <StatusDot
            status={operator?.shift_status === 'ON_SHIFT' ? 'green' : 'gray'}
            pulse={operator?.shift_status === 'ON_SHIFT'}
            label={operator?.shift_status?.replace('_', ' ') ?? 'OFF SHIFT'}
            size="lg"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Quick actions */}
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Watch', icon: Watch, to: '/watch', color: 'text-amber-400' },
            { label: 'Pre-Start', icon: ShieldCheck, to: '/prestart', color: 'text-green-400' },
            { label: 'Alerts', icon: Bell, to: '/alerts', color: 'text-red-400', badge: allAlerts.filter((a) => !a.acknowledged).length },
            { label: 'Training', icon: BookOpen, to: '/training', color: 'text-blue-400' },
          ].map(({ label, icon: Icon, to, color, badge }) => (
            <Link
              key={label}
              to={to}
              className="card hover:border-slate-500 transition-colors text-center py-4"
              aria-label={`Go to ${label}`}
            >
              <div className="relative inline-block">
                <Icon size={22} className={`${color} mx-auto mb-1.5`} />
                {badge !== undefined && badge > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center">
                    {badge}
                  </span>
                )}
              </div>
              <div className="text-xs text-slate-400">{label}</div>
            </Link>
          ))}
        </div>

        {/* Current task */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <ClipboardList size={14} className="text-amber-400" />
              Current Task
            </h2>
            {currentTask && <StatusDot status="amber" pulse label="IN PROGRESS" />}
          </div>
          {currentTask ? (
            <>
              <div className="text-lg font-bold text-slate-100 mb-1">{currentTask.task_type}</div>
              <div className="text-xs text-slate-400 mb-3">
                Zone: {currentTask.zone_id?.slice(0, 12) ?? '—'} · Material: {currentTask.material_type ?? '—'}
              </div>
              {currentTask.target_quantity && (
                <div className="mb-3">
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span>Progress</span>
                    <span>{currentTask.completed_quantity.toFixed(0)} / {currentTask.target_quantity.toFixed(0)} {currentTask.unit}</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-3">
                    <div
                      className="h-3 rounded-full bg-amber-500 transition-all"
                      style={{ width: `${(currentTask.completed_quantity / currentTask.target_quantity) * 100}%` }}
                    />
                  </div>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-slate-700/30 rounded-lg p-2">
                  <div className="text-slate-500">Estimated</div>
                  <div className="text-slate-200 font-medium">{currentTask.estimated_duration_minutes?.toFixed(0) ?? '—'} min</div>
                </div>
                <div className="bg-slate-700/30 rounded-lg p-2">
                  <div className="text-slate-500">AI ETA</div>
                  <div className="text-amber-400 font-medium">{currentTask.predicted_duration_minutes?.toFixed(0) ?? '—'} min</div>
                </div>
              </div>
            </>
          ) : (
            <p className="text-slate-500 text-sm py-3">No active task. Check your task queue.</p>
          )}
        </div>

        {/* Next task */}
        {nextTask && (
          <div className="card border-blue-800/30">
            <div className="text-xs text-slate-500 mb-1">NEXT TASK</div>
            <div className="font-medium text-slate-200">{nextTask.task_type}</div>
            <div className="text-xs text-slate-400 mt-1">Est. {nextTask.estimated_duration_minutes?.toFixed(0) ?? '—'} min · {nextTask.material_type ?? '—'}</div>
          </div>
        )}

        {/* Shift stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="card text-center">
            <div className="text-xl font-bold text-slate-100">{operator?.continuous_operating_minutes?.toFixed(0) ?? 0}</div>
            <div className="text-xs text-slate-500">Operating min</div>
            {operator && operator.continuous_operating_minutes > 80 && (
              <div className="text-xs text-yellow-400 mt-1">⚠ Break due</div>
            )}
          </div>
          <div className="card text-center">
            <div className="text-xl font-bold text-slate-100">{completedToday}</div>
            <div className="text-xs text-slate-500">Tasks done today</div>
          </div>
          <div className="card text-center">
            <div className={`text-xl font-bold ${(operator?.safety_score ?? 100) >= 90 ? 'text-green-400' : 'text-yellow-400'}`}>
              {operator?.safety_score?.toFixed(0) ?? '—'}%
            </div>
            <div className="text-xs text-slate-500">Safety score</div>
          </div>
        </div>

        {/* Active alerts */}
        {allAlerts.length > 0 && (
          <div className="card">
            <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2 mb-3">
              <AlertTriangle size={14} className="text-red-400" />
              My Alerts
            </h2>
            <div className="space-y-2">
              {allAlerts.slice(0, 4).map((a) => (
                <div key={a.alert_id} className={`p-2.5 rounded-lg border text-xs ${
                  a.severity === 'CRITICAL' ? 'border-red-800/50 bg-red-900/20' :
                  a.severity === 'HIGH' ? 'border-orange-800/50 bg-orange-900/10' :
                  'border-slate-700 bg-slate-700/20'
                }`}>
                  <div className="flex items-center gap-2 mb-0.5">
                    <SeverityBadge severity={a.severity} />
                    <span className="text-slate-400">{a.alert_type.replace(/_/g, ' ')}</span>
                  </div>
                  <p className="text-slate-300 text-xs">{a.message}</p>
                  <p className="text-slate-500 mt-0.5">{formatDistanceToNow(new Date(a.timestamp), { addSuffix: true })}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
