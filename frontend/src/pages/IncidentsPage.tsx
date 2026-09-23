import { useQuery } from '@tanstack/react-query'
import { AlertTriangle } from 'lucide-react'
import { incidentsApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'
import SeverityBadge from '../components/ui/SeverityBadge'
import { format } from 'date-fns'

export default function IncidentsPage() {
  const { data: incidents, isLoading } = useQuery({
    queryKey: ['incidents'],
    queryFn: () => incidentsApi.list({ page_size: '50' }),
    refetchInterval: 30_000,
  })

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Incidents" subtitle="Incident logging and investigation tracking" icon={<AlertTriangle size={20} />} />
      <div className="p-6 space-y-3">
        {isLoading && <div className="text-slate-400 text-sm animate-pulse">Loading incidents…</div>}
        {incidents?.length === 0 && <p className="text-slate-500 text-sm text-center py-12">No incidents recorded</p>}
        {incidents?.map((inc) => (
          <div key={inc.incident_id} className="card">
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <SeverityBadge severity={inc.severity} />
                  <span className="text-xs text-slate-400 font-mono">{inc.category}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    inc.status === 'OPEN' ? 'bg-red-900/30 text-red-400' :
                    inc.status === 'INVESTIGATING' ? 'bg-yellow-900/30 text-yellow-400' :
                    'bg-green-900/30 text-green-400'
                  }`}>{inc.status}</span>
                  {inc.is_auto_created && <span className="text-xs text-slate-600">(auto-created)</span>}
                </div>
                <p className="text-sm text-slate-200">{inc.description}</p>
                <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
                  <span>{format(new Date(inc.timestamp), 'dd MMM yyyy HH:mm')}</span>
                  {inc.machine_id && <span>Machine: {inc.machine_id.slice(0, 8)}</span>}
                  {inc.operator_id && <span>Operator: {inc.operator_id.slice(0, 8)}</span>}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
