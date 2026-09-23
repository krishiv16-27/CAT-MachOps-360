import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Truck, Search } from 'lucide-react'
import { machinesApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'
import StatusDot from '../components/ui/StatusDot'

export default function MachinesPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data: machines, isLoading } = useQuery({
    queryKey: ['machines'],
    queryFn: () => machinesApi.list(),
    refetchInterval: 15_000,
  })

  const filtered = machines?.filter((m) => {
    const matchSearch = !search || m.machine_code.toLowerCase().includes(search.toLowerCase()) || m.machine_type.toLowerCase().includes(search.toLowerCase())
    const matchStatus = !statusFilter || m.status === statusFilter
    return matchSearch && matchStatus
  })

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Machines" subtitle="Fleet status and health monitoring" icon={<Truck size={20} />} />
      <div className="p-6 space-y-4">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search machines…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500"
              aria-label="Search machines"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500"
            aria-label="Filter by status"
          >
            <option value="">All statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
            <option value="MAINTENANCE">Maintenance</option>
            <option value="FAULT">Fault</option>
          </select>
        </div>

        {isLoading ? (
          <div className="text-slate-400 text-sm animate-pulse">Loading machines…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-slate-500 border-b border-slate-700">
                  {['Code', 'Type', 'Model', 'Status', 'Health', 'Fuel', 'Temp', 'Operator', 'Hours', 'Auth'].map((h) => (
                    <th key={h} className="pb-3 pr-4 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {filtered?.map((m) => (
                  <tr
                    key={m.machine_id}
                    className="hover:bg-slate-700/20 cursor-pointer"
                    onClick={() => navigate(`/machines/${m.machine_id}`)}
                    role="button"
                    aria-label={`View details for ${m.machine_code}`}
                  >
                    <td className="py-3 pr-4 font-mono text-amber-400 font-medium">{m.machine_code}</td>
                    <td className="py-3 pr-4 text-slate-300">{m.machine_type}</td>
                    <td className="py-3 pr-4 text-slate-400 text-xs">{m.model_name}</td>
                    <td className="py-3 pr-4">
                      <StatusDot
                        status={m.status === 'ACTIVE' ? 'green' : m.status === 'MAINTENANCE' ? 'amber' : 'gray'}
                        label={m.status}
                      />
                    </td>
                    <td className="py-3 pr-4">
                      <span className={m.last_health_score && m.last_health_score >= 90 ? 'text-green-400' : m.last_health_score && m.last_health_score >= 75 ? 'text-yellow-400' : 'text-red-400'}>
                        {m.last_health_score?.toFixed(0) ?? '?'}%
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        <div className="w-12 bg-slate-700 rounded-full h-1.5">
                          <div className="h-1.5 rounded-full bg-amber-500" style={{ width: `${m.last_fuel_level_pct ?? 0}%` }} />
                        </div>
                        <span className="text-xs text-slate-400">{m.last_fuel_level_pct?.toFixed(0) ?? 0}%</span>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-slate-400">{m.last_engine_temp_c?.toFixed(0) ?? '?'}°C</td>
                    <td className="py-3 pr-4 text-slate-500 text-xs">{m.current_operator_id ? m.current_operator_id.slice(0, 8) : '—'}</td>
                    <td className="py-3 pr-4 text-slate-400">{m.engine_hours.toFixed(0)}h</td>
                    <td className="py-3 pr-4">
                      <span className={`text-xs font-medium ${m.authorization_status === 'AUTHORIZED' ? 'text-green-400' : m.authorization_status === 'BLOCKED' ? 'text-red-400' : 'text-yellow-400'}`}>
                        {m.authorization_status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
