import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Settings, Zap, RotateCcw, Play, FlaskConical } from 'lucide-react'
import { simulatorApi, mlApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'

const SCENARIOS = [
  { id: 'NORMAL_OPERATION', label: 'Normal Operation', description: 'Reset to steady-state', color: 'bg-green-700 hover:bg-green-600' },
  { id: 'PROXIMITY_HAZARD', label: 'Proximity Hazard', description: 'Person at 3.5m — CRITICAL alert', color: 'bg-red-700 hover:bg-red-600' },
  { id: 'SEATBELT_VIOLATION', label: 'Seatbelt Violation', description: 'Seatbelt off while moving', color: 'bg-orange-700 hover:bg-orange-600' },
  { id: 'EXCESSIVE_IDLING', label: 'Excessive Idling', description: '25 min idle — LOW alert', color: 'bg-blue-700 hover:bg-blue-600' },
  { id: 'MACHINE_OVERHEATING', label: 'Machine Overheating', description: 'Engine 118°C — CRITICAL', color: 'bg-red-800 hover:bg-red-700' },
  { id: 'HYDRAULIC_ANOMALY', label: 'Hydraulic Anomaly', description: 'Pressure drop — MEDIUM alert', color: 'bg-yellow-700 hover:bg-yellow-600' },
  { id: 'UNUSUAL_OPERATOR_BEHAVIOUR', label: 'Unusual Behaviour', description: 'Anomaly detection triggered', color: 'bg-purple-700 hover:bg-purple-600' },
  { id: 'EXTENDED_SHIFT', label: 'Extended Shift', description: '110 min operation — break rec.', color: 'bg-teal-700 hover:bg-teal-600' },
  { id: 'DASHCAM_PERSON_DETECTION', label: 'Dashcam Detection', description: 'Person in restricted zone', color: 'bg-red-700 hover:bg-red-600' },
  { id: 'PRESTART_FAILURE', label: 'Pre-Start Failure', description: 'Certification expired — BLOCKED', color: 'bg-orange-800 hover:bg-orange-700' },
  { id: 'MAINTENANCE_WARNING', label: 'Maintenance Warning', description: 'Fault E-HYD-042 injected', color: 'bg-yellow-800 hover:bg-yellow-700' },
  { id: 'TASK_DELAY_WEATHER', label: 'Task Delay — Weather', description: 'Heavy rain — ETA +35%', color: 'bg-slate-600 hover:bg-slate-500' },
]

export default function SettingsPage() {
  const [lastResult, setLastResult] = useState<Record<string, unknown> | null>(null)

  const { data: simStatus } = useQuery({
    queryKey: ['simulator-status'],
    queryFn: simulatorApi.status,
    refetchInterval: 10_000,
  })

  const activateMutation = useMutation({
    mutationFn: (scenario: string) => simulatorApi.activate(scenario),
    onSuccess: (data) => setLastResult(data as Record<string, unknown>),
  })

  const resetMutation = useMutation({
    mutationFn: simulatorApi.reset,
    onSuccess: () => setLastResult(null),
  })

  const status = simStatus as Record<string, unknown> | undefined

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Settings & Demo Controls" icon={<Settings size={20} />} />
      <div className="flex-1 overflow-y-auto p-6 space-y-6 max-w-4xl">
        {/* Simulator status */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              <Zap size={16} className="text-amber-400" />
              Demo Scenario Simulator
            </h2>
            <button
              onClick={() => resetMutation.mutate()}
              disabled={resetMutation.isPending}
              className="btn-secondary text-xs flex items-center gap-1.5"
              aria-label="Reset simulator to normal operation"
            >
              <RotateCcw size={12} />
              Reset to Normal
            </button>
          </div>

          {status?.name && (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg px-4 py-2 mb-4 text-sm">
              <span className="text-amber-400 font-medium">Active scenario:</span>{' '}
              <span className="text-slate-200">{status.name as string}</span>
            </div>
          )}

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {SCENARIOS.map((s) => (
              <button
                key={s.id}
                onClick={() => activateMutation.mutate(s.id)}
                disabled={activateMutation.isPending}
                className={`${s.color} text-white text-left px-3 py-3 rounded-xl transition-colors disabled:opacity-50 group`}
                aria-label={`Activate ${s.label} scenario`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <Play size={12} className="flex-shrink-0" />
                  <span className="font-medium text-sm">{s.label}</span>
                </div>
                <p className="text-xs text-white/70">{s.description}</p>
              </button>
            ))}
          </div>

          {lastResult && (
            <div className="mt-4 bg-slate-700/50 rounded-lg p-4 text-xs text-slate-300 font-mono">
              <p className="text-green-400 mb-1">✓ Scenario activated</p>
              <p><span className="text-slate-500">Scenario:</span> {lastResult.scenario as string}</p>
              <p><span className="text-slate-500">Description:</span> {lastResult.description as string}</p>
              <p><span className="text-slate-500">Events injected:</span> {lastResult.events_injected as number}</p>
              <p className="text-slate-500 mt-1">Check the Alerts page and Watch simulator for results.</p>
            </div>
          )}
        </div>

        {/* What-If Simulator */}
        <div className="card">
          <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2 mb-4">
            <FlaskConical size={16} className="text-amber-400" />
            What-If Simulator
          </h2>
          <WhatIfSimulator />
        </div>

        {/* System info */}
        <div className="card">
          <h2 className="text-sm font-semibold text-slate-300 mb-3">System Information</h2>
          <div className="space-y-2 text-sm">
            {[
              { label: 'App Version', value: '1.0.0' },
              { label: 'Build', value: 'Hackathon MVP' },
              { label: 'Dataset', value: 'Synthetic Demo Data (seed=42)' },
              { label: 'ML Models', value: 'Mock mode (run training scripts to activate)' },
              { label: 'RAG', value: 'Mock responses (add LLM key for real responses)' },
            ].map(({ label, value }) => (
              <div key={label} className="flex justify-between py-1 border-b border-slate-700/50">
                <span className="text-slate-500">{label}</span>
                <span className="text-slate-300">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

// ── What-If Simulator ─────────────────────────────────────────────────────────
function WhatIfSimulator() {
  const [weather, setWeather] = useState('CLEAR')
  const [operatorSkill, setOperatorSkill] = useState('3')
  const [load, setLoad] = useState('70')
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [running, setRunning] = useState(false)

  async function estimate() {
    setRunning(true)
    try {
      const baseFeatures = {
        task_type: 'EXCAVATION',
        machine_type: 'EXCAVATOR',
        operator_skill_level: parseInt(operatorSkill),
        weather_condition: weather,
        terrain_type: 'FLAT',
        machine_load_percent: parseInt(load),
        target_quantity: 200,
        machine_age_years: 3,
        operator_experience_years: 6,
        temperature_celsius: weather === 'HEAVY_RAIN' ? 16 : 24,
        rainfall_mm: weather === 'HEAVY_RAIN' ? 25 : weather === 'RAIN' ? 10 : 0,
        wind_speed_kmh: 12,
      }
      const baseRes = await mlApi.predictEta({ ...baseFeatures, weather_condition: 'CLEAR', machine_load_percent: 70, operator_skill_level: 3 })
      const whatifRes = await mlApi.predictEta(baseFeatures)

      const etaChange = whatifRes.predicted_minutes - baseRes.predicted_minutes
      const etaChangePct = (etaChange / baseRes.predicted_minutes) * 100

      // Fuel change estimate
      const loadFactor = parseInt(load) / 70
      const weatherFuelFactor = weather === 'HEAVY_RAIN' ? 1.18 : weather === 'RAIN' ? 1.10 : weather === 'FOG' ? 1.05 : 1.0
      const fuelChange = ((loadFactor * weatherFuelFactor) - 1) * 100

      // Risk change
      const riskChange = weather === 'HEAVY_RAIN' ? '+35%' : weather === 'RAIN' ? '+18%' :
        parseInt(load) > 85 ? '+25%' : parseInt(operatorSkill) < 2 ? '+20%' : 'Minimal'

      setResult({
        baseline_eta: `${baseRes.predicted_minutes.toFixed(0)} min`,
        whatif_eta: `${whatifRes.predicted_minutes.toFixed(0)} min`,
        eta_change: `${etaChange > 0 ? '+' : ''}${etaChange.toFixed(0)} min (${etaChangePct > 0 ? '+' : ''}${etaChangePct.toFixed(0)}%)`,
        fuel_change: `${fuelChange > 0 ? '+' : ''}${fuelChange.toFixed(0)}%`,
        estimated_risk_change: riskChange,
        scenario_summary: `Weather: ${weather} | Load: ${load}% | Skill Level: ${operatorSkill}/5`,
      })
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-slate-400">Estimate the impact of changing conditions on task ETA, fuel consumption, and risk.</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="text-xs text-slate-400 mb-1 block" htmlFor="whatif-weather">Weather condition</label>
          <select
            id="whatif-weather"
            value={weather}
            onChange={(e) => setWeather(e.target.value)}
            className="w-full bg-slate-700 text-slate-200 text-sm px-3 py-2 rounded border border-slate-600 focus:outline-none focus:border-amber-500"
            aria-label="Select weather condition"
          >
            {['CLEAR', 'CLOUDY', 'FOG', 'RAIN', 'HEAVY_RAIN'].map((w) => (
              <option key={w} value={w}>{w.replace('_', ' ')}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs text-slate-400 mb-1 block" htmlFor="whatif-skill">Operator skill level</label>
          <select
            id="whatif-skill"
            value={operatorSkill}
            onChange={(e) => setOperatorSkill(e.target.value)}
            className="w-full bg-slate-700 text-slate-200 text-sm px-3 py-2 rounded border border-slate-600 focus:outline-none focus:border-amber-500"
            aria-label="Select operator skill level"
          >
            {[1, 2, 3, 4, 5].map((s) => <option key={s} value={s}>Level {s} {s === 5 ? '(Expert)' : s === 1 ? '(Novice)' : ''}</option>)}
          </select>
        </div>

        <div>
          <label className="text-xs text-slate-400 mb-1 block" htmlFor="whatif-load">Machine load (%)</label>
          <select
            id="whatif-load"
            value={load}
            onChange={(e) => setLoad(e.target.value)}
            className="w-full bg-slate-700 text-slate-200 text-sm px-3 py-2 rounded border border-slate-600 focus:outline-none focus:border-amber-500"
            aria-label="Select machine load percentage"
          >
            {['40', '60', '70', '80', '90', '100'].map((l) => <option key={l} value={l}>{l}%</option>)}
          </select>
        </div>
      </div>

      <button
        onClick={estimate}
        disabled={running}
        className="btn-primary text-sm flex items-center gap-2 disabled:opacity-50"
        aria-label="Estimate impact of what-if scenario"
      >
        <FlaskConical size={14} />
        {running ? 'Estimating…' : 'Estimate Impact'}
      </button>

      {result && (
        <div className="bg-slate-700/40 rounded-xl p-4 space-y-3">
          <p className="text-xs text-amber-400 font-semibold">Scenario: {result.scenario_summary as string}</p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'ETA Change', value: result.eta_change as string, color: (result.eta_change as string).startsWith('+') ? 'text-red-400' : 'text-green-400' },
              { label: 'Fuel Change', value: result.fuel_change as string, color: (result.fuel_change as string).startsWith('+') ? 'text-red-400' : 'text-green-400' },
              { label: 'Risk Change', value: result.estimated_risk_change as string, color: result.estimated_risk_change !== 'Minimal' ? 'text-amber-400' : 'text-green-400' },
            ].map(({ label, value, color }) => (
              <div key={label} className="bg-slate-800 rounded-lg p-3 text-center">
                <div className={`text-lg font-bold ${color}`}>{value}</div>
                <div className="text-xs text-slate-500">{label}</div>
              </div>
            ))}
          </div>
          <div className="text-xs text-slate-500 flex justify-between">
            <span>Baseline ETA: {result.baseline_eta as string}</span>
            <span>What-if ETA: {result.whatif_eta as string}</span>
          </div>
        </div>
      )}
    </div>
  )
}
