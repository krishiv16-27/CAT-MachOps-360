import { useWatchStore } from '../store/watchStore'
import { useAlertStore } from '../store/alertStore'
import { useAuthStore } from '../store/authStore'
import { useQuery } from '@tanstack/react-query'
import { tasksApi, operatorsApi } from '../services/api'
import { ChevronLeft, ChevronRight, AlertTriangle, Zap } from 'lucide-react'
import { QRCodeSVG } from 'qrcode.react'
import { format } from 'date-fns'
import { alertsApi } from '../services/api'

export default function WatchPage() {
  const { currentScreen, nextScreen, prevScreen, screens, activeAlert, clearAlert, isVibrating } = useWatchStore()
  const { user } = useAuthStore()
  const { alerts } = useAlertStore()

  const screenIndex = screens.indexOf(currentScreen)
  const operatorId = user?.operator_id

  const { data: tasks } = useQuery({
    queryKey: ['tasks', operatorId],
    queryFn: () => tasksApi.list({ operator_id: operatorId!, page_size: '20' }),
    enabled: !!operatorId,
    refetchInterval: 30_000,
  })

  const { data: operator } = useQuery({
    queryKey: ['operator', operatorId],
    queryFn: () => operatorsApi.get(operatorId!),
    enabled: !!operatorId,
  })

  const currentTask = tasks?.find((t) => t.status === 'IN_PROGRESS')
  const nextTask = tasks?.find((t) => t.status === 'PENDING')
  const todayAlerts = alerts.filter((a) => !a.resolved)

  const now = new Date()

  function renderScreen() {
    switch (currentScreen) {
      case 'home':
        return (
          <div className="flex flex-col h-full p-4 gap-3">
            <div className="text-center">
              <div className="text-3xl font-bold font-mono text-white">{format(now, 'HH:mm')}</div>
              <div className="text-xs text-slate-400">{format(now, 'EEE, dd MMM')}</div>
            </div>
            <div className="border-t border-slate-700 pt-3">
              <div className="text-xs text-slate-500">OPERATOR</div>
              <div className="text-sm font-bold text-amber-400">{operator?.name ?? user?.name ?? '—'}</div>
              <div className="text-xs text-slate-500">{operator?.employee_code ?? '—'}</div>
            </div>
            {currentTask && (
              <div className="border-t border-slate-700 pt-3">
                <div className="text-xs text-slate-500">CURRENT TASK</div>
                <div className="text-sm font-bold text-white">{currentTask.task_type}</div>
                {currentTask.target_quantity && (
                  <div className="mt-1">
                    <div className="flex justify-between text-xs text-slate-400 mb-1">
                      <span>Progress</span>
                      <span>{((currentTask.completed_quantity / currentTask.target_quantity) * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2">
                      <div className="h-2 rounded-full bg-amber-500"
                        style={{ width: `${(currentTask.completed_quantity / currentTask.target_quantity) * 100}%` }} />
                    </div>
                  </div>
                )}
                {currentTask.predicted_duration_minutes && (
                  <div className="text-xs text-slate-400 mt-1">
                    ETA: <span className="text-white font-medium">~{currentTask.predicted_duration_minutes.toFixed(0)} min</span>
                  </div>
                )}
              </div>
            )}
            <div className="border-t border-slate-700 pt-3 flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-500">SAFETY</div>
                <div className="text-sm font-bold text-green-400">● SAFE</div>
              </div>
              <div>
                <div className="text-xs text-slate-500">ALERTS</div>
                <div className={`text-sm font-bold ${todayAlerts.length > 0 ? 'text-red-400' : 'text-green-400'}`}>
                  {todayAlerts.length}
                </div>
              </div>
            </div>
          </div>
        )

      case 'current-task':
        return (
          <div className="flex flex-col h-full p-4 gap-3">
            <div className="text-xs text-amber-400 font-bold uppercase tracking-wider">Current Task</div>
            {currentTask ? (
              <>
                <div className="text-xl font-bold text-white">{currentTask.task_type}</div>
                <div className="text-xs text-slate-400">Zone: {currentTask.zone_id?.slice(0, 12) ?? '—'}</div>
                <div className="text-xs text-slate-400">Machine: {currentTask.machine_id?.slice(0, 8) ?? '—'}</div>
                <div className="text-xs text-slate-400">Material: {currentTask.material_type ?? '—'}</div>
                <div className="text-xs text-slate-400">
                  Started: {currentTask.actual_start ? format(new Date(currentTask.actual_start), 'HH:mm') : '—'}
                </div>
                <div className="mt-auto">
                  <div className="text-xs text-slate-500 mb-1">
                    {currentTask.completed_quantity?.toFixed(0)} / {currentTask.target_quantity?.toFixed(0)} {currentTask.unit}
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-3">
                    <div className="h-3 rounded-full bg-amber-500"
                      style={{ width: `${currentTask.target_quantity ? (currentTask.completed_quantity / currentTask.target_quantity) * 100 : 0}%` }} />
                  </div>
                </div>
              </>
            ) : (
              <div className="text-slate-500 text-sm text-center py-8">No active task</div>
            )}
          </div>
        )

      case 'active-alert':
        return (
          <div className={`flex flex-col h-full p-4 gap-3 ${activeAlert?.severity === 'CRITICAL' ? 'bg-red-950' : 'bg-orange-950'}`}>
            <div className="text-center animate-alert-pulse">
              <AlertTriangle size={32} className={activeAlert?.severity === 'CRITICAL' ? 'text-red-400 mx-auto' : 'text-orange-400 mx-auto'} />
              <div className="text-sm font-bold text-white mt-2">
                {activeAlert?.alert_type?.replace(/_/g, ' ') ?? 'ALERT'}
              </div>
              <div className={`text-xs font-bold mt-1 ${activeAlert?.severity === 'CRITICAL' ? 'text-red-400' : 'text-orange-400'}`}>
                {activeAlert?.severity}
              </div>
            </div>
            <div className="text-xs text-slate-300 text-center leading-relaxed">
              {activeAlert?.message ?? 'No active alert'}
            </div>
            {activeAlert?.recommended_action && (
              <div className="text-xs text-slate-400 border border-slate-600 rounded p-2">
                {activeAlert.recommended_action}
              </div>
            )}
            <button
              onClick={clearAlert}
              className="mt-auto w-full py-3 rounded-xl font-bold text-sm bg-white text-slate-900 hover:bg-slate-100"
              aria-label="Acknowledge alert"
            >
              ACKNOWLEDGE
            </button>
          </div>
        )

      case 'machine-status':
        return (
          <div className="flex flex-col h-full p-4 gap-3">
            <div className="text-xs text-amber-400 font-bold uppercase tracking-wider">Machine Status</div>
            <div className="text-lg font-bold text-white">{currentTask?.machine_id?.slice(0, 8) ?? 'No machine assigned'}</div>
            <div className="space-y-2">
              {[
                { label: 'Engine', value: 'RUNNING', color: 'text-green-400' },
                { label: 'Fuel', value: '67%', color: 'text-amber-400' },
                { label: 'Hydraulics', value: 'NORMAL', color: 'text-green-400' },
                { label: 'Health', value: '94%', color: 'text-green-400' },
              ].map(({ label, value, color }) => (
                <div key={label} className="flex justify-between text-sm">
                  <span className="text-slate-400">{label}</span>
                  <span className={`font-bold ${color}`}>{value}</span>
                </div>
              ))}
            </div>
          </div>
        )

      case 'safety-status':
        return (
          <div className="flex flex-col h-full p-4 gap-3">
            <div className="text-xs text-amber-400 font-bold uppercase tracking-wider">Safety Status</div>
            <div className="text-3xl font-bold text-green-400 text-center py-4">● SAFE</div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between"><span className="text-slate-400">Alerts Today</span><span className="text-white">{todayAlerts.length}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Unack'd</span><span className="text-white">{todayAlerts.filter((a) => !a.acknowledged).length}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Safety Score</span><span className="text-green-400">{operator?.safety_score?.toFixed(0) ?? '—'}%</span></div>
            </div>
          </div>
        )

      case 'shift-summary':
        return (
          <div className="flex flex-col h-full p-4 gap-3">
            <div className="text-xs text-amber-400 font-bold uppercase tracking-wider">Shift Summary</div>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between"><span className="text-slate-400">Shift Start</span>
                <span className="text-white">{operator?.shift_start ? format(new Date(operator.shift_start), 'HH:mm') : '—'}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Operating</span>
                <span className="text-white">{operator?.continuous_operating_minutes?.toFixed(0) ?? 0} min</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Tasks Done</span>
                <span className="text-white">{tasks?.filter((t) => t.status === 'COMPLETED').length ?? 0}</span></div>
              <div className="flex justify-between"><span className="text-slate-400">Safety Events</span>
                <span className={todayAlerts.length > 0 ? 'text-yellow-400' : 'text-green-400'}>{todayAlerts.length}</span></div>
            </div>
          </div>
        )

      case 'qr-code':
        return (
          <div className="flex flex-col h-full p-4 items-center gap-3">
            <div className="text-xs text-amber-400 font-bold uppercase tracking-wider">Operator ID</div>
            <div className="bg-white p-3 rounded-xl">
              <QRCodeSVG
                value={JSON.stringify({ operator_id: operatorId ?? 'DEMO', name: user?.name ?? 'Demo' })}
                size={160}
                fgColor="#0f172a"
                bgColor="#ffffff"
              />
            </div>
            <div className="text-xs text-slate-400 text-center">
              {operator?.employee_code ?? user?.email}<br />
              <span className="text-slate-600">ID only — no sensitive data</span>
            </div>
          </div>
        )

      case 'emergency':
        return (
          <div className="flex flex-col h-full p-4 items-center justify-center gap-4">
            <div className="text-xs text-red-400 font-bold uppercase tracking-wider">Emergency</div>
            <button
              className="w-32 h-32 rounded-full bg-red-600 hover:bg-red-500 border-4 border-red-400 flex flex-col items-center justify-center gap-1 shadow-lg shadow-red-900/50 active:scale-95 transition-all"
              onClick={() => { if (typeof navigator !== 'undefined' && navigator.vibrate) navigator.vibrate([1000]) }}
              aria-label="Emergency stop button"
            >
              <AlertTriangle size={28} className="text-white" />
              <span className="text-white font-black text-sm">EMERGENCY</span>
            </button>
            <p className="text-xs text-slate-500 text-center">Press to signal emergency stop and alert supervisor</p>
          </div>
        )

      case 'break-recommendation':
        return (
          <div className="flex flex-col h-full p-4 gap-3">
            <div className="text-xs text-amber-400 font-bold uppercase tracking-wider">Break Status</div>
            {operator && operator.continuous_operating_minutes > 80 ? (
              <>
                <div className="text-yellow-400 font-bold text-lg">⚠ Break Recommended</div>
                <p className="text-sm text-slate-300">You have been operating for {operator.continuous_operating_minutes.toFixed(0)} minutes continuously.</p>
                <p className="text-xs text-slate-400">Recommended: 15 min break</p>
              </>
            ) : (
              <>
                <div className="text-green-400 font-bold text-lg">● No break needed</div>
                <p className="text-sm text-slate-400">
                  Operating: {operator?.continuous_operating_minutes?.toFixed(0) ?? 0} min<br />
                  Next recommendation at 90 min
                </p>
              </>
            )}
          </div>
        )

      case 'training':
        return (
          <div className="flex flex-col h-full p-4 gap-3">
            <div className="text-xs text-amber-400 font-bold uppercase tracking-wider">Training</div>
            <div className="text-sm text-slate-300">Your pending training modules:</div>
            <div className="space-y-2">
              {['Proximity Safety Awareness', 'Pre-Start Inspection'].map((t) => (
                <div key={t} className="bg-slate-700/50 rounded-lg p-2 text-xs text-slate-300 border border-slate-600">{t}</div>
              ))}
            </div>
            <div className="text-xs text-slate-500 mt-auto">Complete modules on the Training hub page</div>
          </div>
        )

      default:
        return <div className="p-4 text-slate-400 text-sm text-center">Screen: {currentScreen}</div>
    }
  }

  const SCREEN_LABELS: Record<string, string> = {
    'home': 'Home', 'current-task': 'Task', 'task-progress': 'Progress',
    'next-task': 'Next Task', 'safety-status': 'Safety', 'active-alert': 'Alert',
    'break-recommendation': 'Break', 'machine-status': 'Machine', 'emergency': 'SOS',
    'shift-summary': 'Shift', 'todays-tasks': 'Today', 'safety-events': 'Events',
    'qr-code': 'QR', 'training': 'Training',
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-slate-900 p-4">
      <h1 className="text-sm font-medium text-slate-400 mb-4 uppercase tracking-wider">Smart Watch Simulator</h1>

      {/* Watch frame */}
      <div className={`relative w-72 transition-all duration-200 ${isVibrating ? 'animate-pulse' : ''}`}>
        {/* Outer bezel */}
        <div className={`rounded-[40px] p-1.5 shadow-2xl ${
          activeAlert?.severity === 'CRITICAL' ? 'bg-red-500 shadow-red-900/50' :
          activeAlert?.severity === 'HIGH' ? 'bg-orange-500 shadow-orange-900/50' :
          'bg-amber-500 shadow-amber-900/30'
        }`}>
          {/* Inner watch */}
          <div className="bg-slate-950 rounded-[32px] overflow-hidden"
            style={{ minHeight: '360px' }}>
            {/* Status bar */}
            <div className="flex items-center justify-between px-4 py-2 bg-slate-900/80">
              <span className="text-xs font-mono text-slate-400">{format(now, 'HH:mm')}</span>
              <div className="flex items-center gap-1">
                <Zap size={10} className="text-amber-400" />
                <span className="text-xs text-slate-400">87%</span>
              </div>
            </div>

            {/* Screen content */}
            <div className="px-0" style={{ minHeight: '300px' }}>
              {renderScreen()}
            </div>

            {/* Nav dots */}
            <div className="flex justify-center gap-1.5 pb-3 pt-1">
              {screens.map((s, i) => (
                <button
                  key={s}
                  onClick={() => useWatchStore.getState().setScreen(s)}
                  className={`rounded-full transition-all ${i === screenIndex ? 'w-4 h-1.5 bg-amber-400' : 'w-1.5 h-1.5 bg-slate-600'}`}
                  aria-label={`Go to ${SCREEN_LABELS[s]} screen`}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Side crown/button */}
        <div className="absolute -right-2 top-1/3 w-2 h-8 bg-slate-600 rounded-r-lg" aria-hidden="true" />
      </div>

      {/* Navigation */}
      <div className="flex items-center gap-4 mt-6">
        <button onClick={prevScreen} className="btn-secondary flex items-center gap-1 text-sm" aria-label="Previous watch screen">
          <ChevronLeft size={16} />
          Prev
        </button>
        <span className="text-xs text-slate-500 w-28 text-center">{SCREEN_LABELS[currentScreen] ?? currentScreen}</span>
        <button onClick={nextScreen} className="btn-secondary flex items-center gap-1 text-sm" aria-label="Next watch screen">
          Next
          <ChevronRight size={16} />
        </button>
      </div>

      {/* Screen quick-jump */}
      <div className="mt-4 grid grid-cols-4 gap-2 max-w-xs">
        {screens.slice(0, 8).map((s) => (
          <button
            key={s}
            onClick={() => useWatchStore.getState().setScreen(s)}
            className={`text-xs px-2 py-1.5 rounded-lg transition-colors ${
              s === currentScreen ? 'bg-amber-500 text-slate-900 font-bold' : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
            }`}
            aria-label={`Jump to ${SCREEN_LABELS[s]}`}
          >
            {SCREEN_LABELS[s]}
          </button>
        ))}
      </div>

      <p className="text-xs text-slate-600 mt-4">Browser vibration API active on supported devices</p>
    </div>
  )
}
