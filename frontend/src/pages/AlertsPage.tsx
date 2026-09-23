import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bell, Check } from 'lucide-react'
import { alertsApi } from '../services/api'
import { useAlertStore } from '../store/alertStore'
import PageHeader from '../components/ui/PageHeader'
import SeverityBadge from '../components/ui/SeverityBadge'
import { formatDistanceToNow } from 'date-fns'

export default function AlertsPage() {
  const [severityFilter, setSeverityFilter] = useState('')
  const [showResolved, setShowResolved] = useState(false)
  const { alerts: wsAlerts } = useAlertStore()
  const qc = useQueryClient()

  const { data: alerts, isLoading } = useQuery({
    queryKey: ['alerts', severityFilter, showResolved],
    queryFn: () => alertsApi.list({
      ...(severityFilter ? { severity: severityFilter } : {}),
      resolved: String(showResolved),
    }),
    refetchInterval: 10_000,
  })

  const ackMutation = useMutation({
    mutationFn: (alertId: string) => alertsApi.acknowledge(alertId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['alerts'] }),
  })

  const displayAlerts = alerts ?? wsAlerts

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Alerts"
        subtitle={`${displayAlerts.filter((a) => !a.acknowledged).length} unacknowledged`}
        icon={<Bell size={20} />}
      />
      <div className="p-6 space-y-4">
        <div className="flex gap-3">
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500"
            aria-label="Filter by severity"
          >
            <option value="">All severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={showResolved}
              onChange={(e) => setShowResolved(e.target.checked)}
              className="accent-amber-500"
            />
            Show resolved
          </label>
        </div>

        {isLoading && <div className="text-slate-400 text-sm animate-pulse">Loading alerts…</div>}

        <div className="space-y-3">
          {displayAlerts.length === 0 && (
            <div className="text-center py-12 text-slate-500">
              <Bell size={32} className="mx-auto mb-2 opacity-30" />
              <p>No alerts found</p>
            </div>
          )}
          {displayAlerts.map((a) => (
            <div key={a.alert_id} className={`p-4 rounded-xl border transition-all ${
              a.severity === 'CRITICAL' ? 'bg-red-900/20 border-red-800/50' :
              a.severity === 'HIGH' ? 'bg-orange-900/20 border-orange-800/50' :
              a.severity === 'MEDIUM' ? 'bg-yellow-900/10 border-yellow-800/30' :
              'bg-slate-700/20 border-slate-700'
            }`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <SeverityBadge severity={a.severity} />
                    <span className="text-xs font-mono text-slate-400">{a.alert_type.replace(/_/g, ' ')}</span>
                    {a.machine_id && <span className="text-xs text-slate-500">· Machine: {a.machine_id.slice(0, 8)}</span>}
                  </div>
                  <p className="text-sm text-slate-200">{a.message}</p>
                  {a.recommended_action && (
                    <p className="text-xs text-slate-400 mt-1 border-l-2 border-slate-600 pl-2">{a.recommended_action}</p>
                  )}
                  <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                    <span>{formatDistanceToNow(new Date(a.timestamp), { addSuffix: true })}</span>
                    {a.acknowledged ? (
                      <span className="text-green-400 flex items-center gap-1"><Check size={10} /> Acknowledged</span>
                    ) : (
                      <span className="text-yellow-400">Awaiting acknowledgement</span>
                    )}
                  </div>
                </div>
                {!a.acknowledged && (
                  <button
                    onClick={() => ackMutation.mutate(a.alert_id)}
                    disabled={ackMutation.isPending}
                    className="btn-secondary text-xs flex-shrink-0"
                    aria-label={`Acknowledge alert ${a.alert_id}`}
                  >
                    Acknowledge
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
