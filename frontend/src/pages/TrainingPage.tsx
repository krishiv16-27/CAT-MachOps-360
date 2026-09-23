import { useQuery } from '@tanstack/react-query'
import { GraduationCap, Play, Clock } from 'lucide-react'
import { trainingApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'

const CATEGORY_COLOR: Record<string, string> = {
  SAFETY: 'text-red-400 bg-red-900/20',
  MACHINE_OPERATION: 'text-amber-400 bg-amber-900/20',
  CERTIFICATION: 'text-blue-400 bg-blue-900/20',
  ENVIRONMENT: 'text-green-400 bg-green-900/20',
  EMERGENCY: 'text-purple-400 bg-purple-900/20',
}

export default function TrainingPage() {
  const { data: modules, isLoading } = useQuery({
    queryKey: ['training-modules'],
    queryFn: trainingApi.modules,
  })

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Training Hub" subtitle="Safety modules, machine operation, and certification" icon={<GraduationCap size={20} />} />
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading && <div className="text-slate-400 text-sm animate-pulse">Loading modules…</div>}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {(modules as Record<string, unknown>[] | undefined)?.map((m) => (
            <div key={m.module_id as string} className="card hover:border-amber-500/30 transition-colors">
              <div className="flex items-start justify-between mb-3">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${CATEGORY_COLOR[m.category as string] ?? 'text-slate-400 bg-slate-700'}`}>
                  {m.category as string}
                </span>
                <span className="text-xs text-slate-500 flex items-center gap-1">
                  <Clock size={10} />
                  {m.duration_minutes as number} min
                </span>
              </div>
              <h3 className="font-medium text-slate-200 text-sm mb-1">{m.title as string}</h3>
              {m.description && <p className="text-xs text-slate-400 mb-3">{m.description as string}</p>}
              <div className="flex items-center justify-between">
                <div className="flex gap-2">
                  <span className="text-xs text-slate-500">{m.module_type as string}</span>
                  {m.is_mandatory && <span className="text-xs text-red-400">Required</span>}
                </div>
                <button className="btn-primary text-xs flex items-center gap-1 py-1.5 px-3" aria-label={`Start ${m.title} training module`}>
                  <Play size={10} />
                  Start
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
