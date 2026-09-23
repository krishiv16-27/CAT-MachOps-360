import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { ShieldCheck, CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { machinesApi, operatorsApi, prestartApi } from '../services/api'
import { useAuthStore } from '../store/authStore'
import PageHeader from '../components/ui/PageHeader'
import type { PrestartResult } from '../types'

export default function PrestartPage() {
  const { user } = useAuthStore()
  const [selectedMachine, setSelectedMachine] = useState('')
  const [selectedOperator, setSelectedOperator] = useState(user?.operator_id ?? '')
  const [checklist, setChecklist] = useState<Record<string, boolean>>({})
  const [result, setResult] = useState<PrestartResult | null>(null)

  const { data: machines } = useQuery({ queryKey: ['machines'], queryFn: () => machinesApi.list() })
  const { data: operators } = useQuery({
    queryKey: ['operators'],
    queryFn: () => operatorsApi.list(),
    enabled: user?.role !== 'operator',
  })

  const { data: checklistData, isLoading: checklistLoading } = useQuery({
    queryKey: ['prestart-checklist', selectedMachine, selectedOperator],
    queryFn: () => prestartApi.getChecklist(selectedMachine, selectedOperator),
    enabled: !!(selectedMachine && selectedOperator),
  })

  const submitMutation = useMutation({
    mutationFn: () =>
      prestartApi.submit({
        machine_id: selectedMachine,
        operator_id: selectedOperator,
        items: (checklistData as Record<string, unknown>)?.items
          ? ((checklistData as Record<string, unknown>).items as Array<Record<string, unknown>>).map((item) => ({
              item_id: item.item_id,
              passed: checklist[item.item_id as string] ?? item.passed,
              note: null,
            }))
          : [],
      }),
    onSuccess: (data) => setResult(data as unknown as PrestartResult),
  })

  const items = (checklistData as Record<string, unknown>)?.items as Array<Record<string, unknown>> | undefined

  function toggleItem(itemId: string, currentValue: boolean) {
    setChecklist((prev) => ({ ...prev, [itemId]: !currentValue }))
  }

  function getItemPassed(item: Record<string, unknown>): boolean {
    return checklist[item.item_id as string] ?? (item.passed as boolean)
  }

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Pre-Start Machine Check"
        subtitle="Complete checklist before machine authorization"
        icon={<ShieldCheck size={20} />}
      />
      <div className="flex-1 overflow-y-auto p-6 max-w-2xl mx-auto w-full">
        {/* Machine & Operator selection */}
        {!result && (
          <div className="card mb-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">Machine</label>
              <select
                value={selectedMachine}
                onChange={(e) => { setSelectedMachine(e.target.value); setResult(null) }}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500"
                aria-label="Select machine"
              >
                <option value="">Select a machine…</option>
                {machines?.filter((m) => m.status !== 'MAINTENANCE').map((m) => (
                  <option key={m.machine_id} value={m.machine_id}>{m.machine_code} — {m.machine_type}</option>
                ))}
              </select>
            </div>
            {user?.role !== 'operator' && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Operator</label>
                <select
                  value={selectedOperator}
                  onChange={(e) => setSelectedOperator(e.target.value)}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500"
                  aria-label="Select operator"
                >
                  <option value="">Select an operator…</option>
                  {operators?.map((op) => (
                    <option key={op.operator_id} value={op.operator_id}>{op.name} — {op.employee_code}</option>
                  ))}
                </select>
              </div>
            )}
          </div>
        )}

        {/* Pre-filled preliminary status */}
        {checklistData && !result && (
          <div className={`card mb-4 border ${
            (checklistData as Record<string, unknown>).preliminary_status === 'AUTHORIZED' ? 'border-green-800/50' :
            (checklistData as Record<string, unknown>).preliminary_status === 'BLOCKED' ? 'border-red-800/50' :
            'border-yellow-800/50'
          }`}>
            <div className="text-xs text-slate-500 mb-1">Preliminary system check</div>
            <div className={`font-bold ${
              (checklistData as Record<string, unknown>).preliminary_status === 'AUTHORIZED' ? 'text-green-400' :
              (checklistData as Record<string, unknown>).preliminary_status === 'BLOCKED' ? 'text-red-400' :
              'text-yellow-400'
            }`}>{(checklistData as Record<string, unknown>).preliminary_status as string}</div>
          </div>
        )}

        {/* Checklist items */}
        {items && !result && (
          <div className="card mb-6">
            <h3 className="text-sm font-semibold text-slate-300 mb-4">Checklist</h3>
            <div className="space-y-3">
              {items.map((item) => {
                const passed = getItemPassed(item)
                return (
                  <div
                    key={item.item_id as string}
                    className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                      passed ? 'border-green-800/30 bg-green-900/10' : 'border-red-800/30 bg-red-900/10'
                    }`}
                    onClick={() => toggleItem(item.item_id as string, passed)}
                    role="checkbox"
                    aria-checked={passed}
                    aria-label={item.label as string}
                  >
                    {passed
                      ? <CheckCircle2 size={18} className="text-green-400 flex-shrink-0" />
                      : <XCircle size={18} className="text-red-400 flex-shrink-0" />
                    }
                    <div className="flex-1">
                      <span className="text-sm text-slate-200">{item.label as string}</span>
                      {!item.required && <span className="text-xs text-slate-500 ml-2">(optional)</span>}
                      {item.blocked_reason && (
                        <div className="text-xs text-red-400 mt-0.5">{item.blocked_reason as string}</div>
                      )}
                      {item.auto_checked && <span className="text-xs text-slate-500 ml-2">auto-checked</span>}
                    </div>
                  </div>
                )
              })}
            </div>

            <button
              onClick={() => submitMutation.mutate()}
              disabled={!selectedMachine || !selectedOperator || submitMutation.isPending}
              className="btn-primary w-full mt-4 disabled:opacity-50"
              aria-label="Submit pre-start checklist"
            >
              {submitMutation.isPending ? 'Submitting…' : 'Submit Checklist'}
            </button>
          </div>
        )}

        {/* Authorization result */}
        {result && (
          <div className={`card border-2 ${
            result.authorization_status === 'AUTHORIZED' ? 'border-green-500 bg-green-900/20' :
            result.authorization_status === 'BLOCKED' ? 'border-red-500 bg-red-900/20' :
            'border-yellow-500 bg-yellow-900/20'
          }`}>
            <div className="text-center py-4">
              {result.authorization_status === 'AUTHORIZED' && <CheckCircle2 size={48} className="text-green-400 mx-auto mb-3" />}
              {result.authorization_status === 'BLOCKED' && <XCircle size={48} className="text-red-400 mx-auto mb-3" />}
              {result.authorization_status === 'REVIEW' && <AlertCircle size={48} className="text-yellow-400 mx-auto mb-3" />}
              <div className={`text-2xl font-bold mb-2 ${
                result.authorization_status === 'AUTHORIZED' ? 'text-green-400' :
                result.authorization_status === 'BLOCKED' ? 'text-red-400' : 'text-yellow-400'
              }`}>
                {result.authorization_status}
              </div>
              {result.blocked_reasons.length > 0 && (
                <div className="mt-3 text-left space-y-1">
                  {result.blocked_reasons.map((r, i) => (
                    <p key={i} className="text-sm text-red-300">✗ {r}</p>
                  ))}
                </div>
              )}
              {result.authorization_status === 'AUTHORIZED' && (
                <p className="text-sm text-green-300 mt-2">All required checks passed. Machine session can begin.</p>
              )}
            </div>
            <button onClick={() => setResult(null)} className="btn-secondary w-full mt-2">
              New Check
            </button>
          </div>
        )}

        {checklistLoading && (
          <div className="text-slate-400 text-sm animate-pulse text-center py-8">Loading checklist…</div>
        )}
        {!selectedMachine && (
          <div className="text-center py-12 text-slate-500">
            <ShieldCheck size={32} className="mx-auto mb-2 opacity-30" />
            <p>Select a machine to begin pre-start check</p>
          </div>
        )}
      </div>
    </div>
  )
}
