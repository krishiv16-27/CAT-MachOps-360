import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Users, Search } from 'lucide-react'
import { operatorsApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'
import StatusDot from '../components/ui/StatusDot'

export default function OperatorsPage() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')

  const { data: operators, isLoading } = useQuery({
    queryKey: ['operators'],
    queryFn: () => operatorsApi.list(),
    refetchInterval: 30_000,
  })

  const filtered = operators?.filter((op) =>
    !search ||
    op.name.toLowerCase().includes(search.toLowerCase()) ||
    op.employee_code.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Operators" subtitle="Workforce monitoring and operator 360 profiles" icon={<Users size={20} />} />
      <div className="p-6 space-y-4">
        <div className="relative max-w-sm">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search operators…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-700 border border-slate-600 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500"
            aria-label="Search operators"
          />
        </div>
        {isLoading ? (
          <div className="text-slate-400 text-sm animate-pulse">Loading operators…</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filtered?.map((op) => (
              <button
                key={op.operator_id}
                className="card text-left hover:border-amber-500/50 transition-colors cursor-pointer"
                onClick={() => navigate(`/operators/${op.operator_id}`)}
                aria-label={`View ${op.name} operator 360 profile`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-9 h-9 bg-amber-500/20 rounded-full flex items-center justify-center text-amber-400 font-bold text-sm">
                      {op.name[0]}
                    </div>
                    <div>
                      <div className="font-medium text-slate-200 text-sm">{op.name}</div>
                      <div className="text-xs text-slate-500">{op.employee_code}</div>
                    </div>
                  </div>
                  <StatusDot
                    status={op.shift_status === 'ON_SHIFT' ? 'green' : op.shift_status === 'ON_BREAK' ? 'amber' : 'gray'}
                    pulse={op.shift_status === 'ON_SHIFT'}
                  />
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs text-slate-500">
                  <span>Exp: <span className="text-slate-300">{op.experience_years}yr · L{op.skill_level}</span></span>
                  <span>Safety: <span className={op.safety_score >= 90 ? 'text-green-400' : op.safety_score >= 75 ? 'text-yellow-400' : 'text-red-400'}>{op.safety_score?.toFixed(0)}%</span></span>
                  <span>Cert: <span className="text-slate-300 truncate">{op.certification ?? '—'}</span></span>
                  <span>Auth: <span className={op.authorization_status === 'AUTHORIZED' ? 'text-green-400' : 'text-red-400'}>{op.authorization_status}</span></span>
                </div>
                {op.continuous_operating_minutes > 80 && (
                  <div className="mt-2 text-xs text-yellow-400 bg-yellow-900/20 rounded px-2 py-1">
                    ⚠ {op.continuous_operating_minutes.toFixed(0)} min continuous operation
                  </div>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
