import { useParams } from 'react-router-dom'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { User, Shield, Clock, Brain, Leaf, AlertTriangle, ChevronDown, ChevronUp, Zap } from 'lucide-react'
import { operatorsApi, mlApi, operatorExtrasApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'
import StatusDot from '../components/ui/StatusDot'
import SeverityBadge from '../components/ui/SeverityBadge'
import ExplainThis from '../components/ui/ExplainThis'
import { format } from 'date-fns'

export default function OperatorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [narrativeOpen, setNarrativeOpen] = useState(false)

  const { data: operator } = useQuery({
    queryKey: ['operator', id],
    queryFn: () => operatorsApi.get(id!),
    enabled: !!id,
  })

  const { data: safetyScore } = useQuery({
    queryKey: ['safety-score', id],
    queryFn: () => operatorsApi.safetyScore(id!),
    enabled: !!id,
  })

  const { data: timeline } = useQuery({
    queryKey: ['operator-timeline', id],
    queryFn: () => operatorsApi.timeline(id!),
    enabled: !!id,
  })

  const { data: recommendations } = useQuery({
    queryKey: ['recommendations', id],
    queryFn: () => operatorsApi.recommendations(id!),
    enabled: !!id,
  })

  const { data: anomaly } = useQuery({
    queryKey: ['anomaly', id],
    queryFn: () => mlApi.anomalyCheck(id!),
    enabled: !!id,
    refetchInterval: 60_000,
  })

  const { data: narrativeData } = useQuery({
    queryKey: ['shift-narrative', id],
    queryFn: () => operatorExtrasApi.shiftNarrative(id!),
    enabled: !!id,
  })

  const { data: carbonData } = useQuery({
    queryKey: ['carbon-passport', id],
    queryFn: () => operatorExtrasApi.carbonPassport(id!),
    enabled: !!id,
  })

  const { data: nearMissData } = useQuery({
    queryKey: ['near-misses', id],
    queryFn: () => operatorExtrasApi.nearMisses(id!),
    enabled: !!id,
  })

  if (!operator) return <div className="p-6 text-slate-400 animate-pulse">Loading operator profile…</div>

  const score = safetyScore as Record<string, unknown> | undefined
  const carbon = carbonData as Record<string, unknown> | undefined
  const nearMiss = nearMissData as Record<string, unknown> | undefined
  const narrative = narrativeData as Record<string, unknown> | undefined

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title={operator.name}
        subtitle={`${operator.employee_code} · ${operator.experience_years}yr experience · Level ${operator.skill_level}`}
        icon={<User size={20} />}
        actions={
          <StatusDot
            status={operator.shift_status === 'ON_SHIFT' ? 'green' : operator.shift_status === 'ON_BREAK' ? 'amber' : 'gray'}
            pulse={operator.shift_status === 'ON_SHIFT'}
            label={operator.shift_status.replace('_', ' ')}
          />
        }
      />

      <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left: Identity + scores */}
        <div className="space-y-4">
          {/* Identity card */}
          <div className="card space-y-3">
            <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <User size={14} className="text-amber-400" />
              Operator Profile
            </h3>
            {[
              { label: 'Employee Code', value: operator.employee_code },
              { label: 'Certification', value: operator.certification ?? '—' },
              { label: 'Cert Expiry', value: operator.certification_expiry ? format(new Date(operator.certification_expiry), 'dd MMM yyyy') : '—' },
              { label: 'Skill Level', value: `Level ${operator.skill_level} / 5` },
              { label: 'Authorization', value: operator.authorization_status },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between text-sm">
                <span className="text-slate-500">{label}</span>
                <span className="text-slate-200 font-medium">{value}</span>
              </div>
            ))}
          </div>

          {/* Safety score */}
          {score && (
            <div className="card">
              <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2 mb-3">
                <Shield size={14} className="text-amber-400" />
                Operational Safety Score (Demo Index)
              </h3>
              <div className="flex items-baseline gap-1 mb-1">
                <div className="text-3xl font-bold text-amber-400">
                  {(score.overall as number)?.toFixed(1)}%
                </div>
                <ExplainThis
                  title="Operational Safety Score (Demo Index)"
                  summary="Weighted composite of 6 compliance and incident factors. Not a validated safety certification."
                  components={
                    score.components
                      ? Object.entries(score.components as Record<string, { score: number; weight: number }>).map(([k, v]) => ({
                          label: k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
                          score: v.score,
                          weight: v.weight,
                        }))
                      : []
                  }
                  disclaimer="Operational Safety Score (Demo Index) — not a validated safety metric. For demonstration purposes only."
                />
              </div>
              <div className="text-xs text-slate-500 mb-3">{score.label as string}</div>
              {score.components && Object.entries(score.components as Record<string, { score: number; weight: number }>).map(([k, v]) => (
                <div key={k} className="mb-2">
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</span>
                    <span className={v.score >= 90 ? 'text-green-400' : v.score >= 75 ? 'text-yellow-400' : 'text-red-400'}>{v.score?.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-slate-700 rounded-full h-1.5">
                    <div className={`h-1.5 rounded-full ${v.score >= 90 ? 'bg-green-500' : v.score >= 75 ? 'bg-yellow-500' : 'bg-red-500'}`}
                      style={{ width: `${v.score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Anomaly status */}
          {anomaly && (
            <div className={`card border ${anomaly.label === 'UNUSUAL' ? 'border-yellow-800/50 bg-yellow-900/10' : 'border-green-800/50'}`}>
              <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2 mb-2">
                <Brain size={14} className="text-amber-400" />
                Behaviour Analysis
              </h3>
              <div className="flex items-center gap-1">
                <span className={`text-sm font-bold ${anomaly.label === 'UNUSUAL' ? 'text-yellow-400' : 'text-green-400'}`}>
                  {anomaly.label}
                </span>
                <ExplainThis
                  title="Behaviour Analysis (ML Anomaly)"
                  summary="IsolationForest model trained on operator telemetry patterns. Detects unusual operating behaviour vs personal and fleet baselines."
                  components={[
                    { label: 'Idle Duration', detail: 'Minutes idle vs operator baseline', value: 'Analysed' },
                    { label: 'Sudden Accelerations', detail: 'Count in last 30 telemetry readings', value: 'Analysed' },
                    { label: 'Fuel Consumption Rate', detail: 'L/h vs expected for load/conditions', value: 'Analysed' },
                    { label: 'Cycle Time', detail: 'Minutes per task cycle vs baseline', value: 'Analysed' },
                    { label: 'Speed Profile', detail: 'Avg and max speed patterns', value: 'Analysed' },
                  ]}
                  disclaimer="Anomaly label uses neutral language. 'UNUSUAL' means operating pattern differs from baseline — not a safety judgment. Not a medical assessment."
                />
              </div>
              <p className="text-xs text-slate-400 mt-1">{anomaly.reason}</p>
              {anomaly.mock && <p className="text-xs text-slate-600 mt-1">Demo — ML model not trained</p>}
            </div>
          )}

          {/* Near-Miss Counter */}
          {nearMiss && (
            <div className={`card border ${(nearMiss.self_corrected_count as number) > 0 ? 'border-green-700/50 bg-green-900/10' : 'border-slate-700'}`}>
              <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2 mb-2">
                <AlertTriangle size={14} className="text-green-400" />
                Near-Miss Counter
              </h3>
              <div className="text-2xl font-bold text-green-400 mb-1">{nearMiss.self_corrected_count as number}</div>
              <p className="text-xs text-slate-300">{nearMiss.badge_text as string}</p>
              <p className="text-xs text-slate-500 mt-1">Site average: {nearMiss.site_average as number}/week</p>
            </div>
          )}

          {/* Carbon Passport */}
          {carbon && (
            <div className="card border border-green-800/40 bg-green-900/10">
              <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2 mb-2">
                <Leaf size={14} className="text-green-400" />
                Carbon Passport
              </h3>
              <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                <div>
                  <div className="text-green-400 font-bold text-lg">{(carbon.shift_co2_saved_kg as number)?.toFixed(1)} kg</div>
                  <div className="text-slate-500">CO₂ saved this shift</div>
                </div>
                <div>
                  <div className="text-amber-400 font-bold text-lg">{carbon.site_rank_percentile as number}%</div>
                  <div className="text-slate-500">Site percentile</div>
                </div>
              </div>
              <p className="text-xs text-slate-400">{carbon.message as string}</p>
            </div>
          )}
        </div>

        {/* Center: Timeline */}
        <div className="xl:col-span-2 space-y-4">
          {/* Shift Narrative */}
          {narrative && (
            <div className="card border border-amber-800/40">
              <button
                onClick={() => setNarrativeOpen(!narrativeOpen)}
                className="w-full flex items-center justify-between text-sm font-semibold text-slate-300"
                aria-label="Toggle shift narrative"
              >
                <span className="flex items-center gap-2">
                  <Zap size={14} className="text-amber-400" />
                  Today's Shift Story
                </span>
                {narrativeOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              </button>
              {narrativeOpen && (
                <div className="mt-3 space-y-3">
                  <p className="text-sm text-slate-300 leading-relaxed">{narrative.narrative as string}</p>
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    {Object.entries((narrative.metrics as Record<string, unknown>) ?? {}).slice(0, 6).map(([k, v]) => (
                      <div key={k} className="bg-slate-700/40 rounded p-2">
                        <div className="text-slate-400 capitalize">{k.replace(/_/g, ' ')}</div>
                        <div className="text-slate-200 font-medium">{v !== null ? String(v) : '—'}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Shift summary */}
          <div className="card">
            <h3 className="text-sm font-semibold text-slate-300 flex items-center gap-2 mb-3">
              <Clock size={14} className="text-amber-400" />
              Today's Summary
            </h3>
            {timeline?.totals && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: 'Operating', value: `${timeline.totals.operating_minutes?.toFixed(0)} min` },
                  { label: 'Break', value: `${timeline.totals.break_minutes?.toFixed(0)} min` },
                  { label: 'Tasks Done', value: `${timeline.totals.tasks_completed} / ${timeline.totals.tasks_total}` },
                  { label: 'Safety Events', value: timeline.totals.safety_events },
                ].map(({ label, value }) => (
                  <div key={label} className="bg-slate-700/30 rounded-lg p-3 text-center">
                    <div className="text-lg font-bold text-slate-100">{value}</div>
                    <div className="text-xs text-slate-500">{label}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Timeline */}
          <div className="card">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Daily Timeline</h3>
            {timeline?.entries?.length === 0 && <p className="text-slate-500 text-sm">No activity recorded today.</p>}
            <div className="space-y-2">
              {timeline?.entries?.map((entry, i) => (
                <div key={i} className={`flex gap-3 p-3 rounded-lg border-l-2 ${
                  entry.entry_type === 'TASK' ? 'border-amber-500 bg-amber-900/10' :
                  entry.entry_type === 'BREAK' ? 'border-blue-500 bg-blue-900/10' :
                  'border-red-500 bg-red-900/10'
                }`}>
                  <div className="text-xs text-slate-500 w-20 flex-shrink-0">
                    {format(new Date(entry.start_time), 'HH:mm')}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-slate-200">{entry.label}</div>
                    <div className="text-xs text-slate-500">
                      {entry.duration_minutes?.toFixed(0)} min
                      {entry.machine_id && ` · ${entry.machine_id.slice(0, 8)}`}
                      {entry.status && ` · ${entry.status}`}
                    </div>
                  </div>
                  {entry.entry_type === 'SAFETY_EVENT' && entry.status && (
                    <SeverityBadge severity={entry.status} />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Training recommendations */}
          {recommendations && recommendations.length > 0 && (
            <div className="card">
              <h3 className="text-sm font-semibold text-slate-300 mb-3">Training Recommendations</h3>
              {recommendations.map((rec, i) => (
                <div key={i} className="p-3 bg-slate-700/30 rounded-lg mb-2">
                  <div className="flex items-center gap-2 mb-1">
                    <SeverityBadge severity={(rec.priority as string) ?? 'MEDIUM'} />
                    <span className="text-sm font-medium text-slate-200">{rec.title as string}</span>
                  </div>
                  <p className="text-xs text-slate-400">{rec.reason as string}</p>
                  {rec.due_date && <p className="text-xs text-slate-500 mt-1">Due: {rec.due_date as string}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
