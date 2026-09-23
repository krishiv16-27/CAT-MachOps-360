/**
 * Live Bird's-Eye Jobsite Safety Map
 * SVG canvas showing machines, workers, zones with real-time proximity detection.
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MapPin, Users, Truck, AlertTriangle, Play, RefreshCw } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import { useAuthStore } from '../store/authStore'
import { useAlertStore } from '../store/alertStore'
import StatusDot from '../components/ui/StatusDot'

const BASE = '/api/v1'
function authHeaders() {
  const token = useAuthStore.getState().token ?? ''
  return { Authorization: `Bearer ${token}` }
}

interface Zone { id: string; x: number; y: number; w: number; h: number; type: string; label: string }
interface MachinePos {
  machine_id: string; machine_code: string; machine_type: string; status: string
  x: number; y: number; current_operator_name: string | null; health_score: number | null
  speed_kmh: number; proximity_warning_radius_px: number; proximity_critical_radius_px: number
}
interface Worker {
  worker_id: string; label: string; x: number; y: number; zone: string
  proximity_status: string; nearest_machine?: string; distance_m?: number
}
interface SiteMapData {
  zones: Zone[]; machines: MachinePos[]; workers: Worker[]
  proximity_alerts: { worker_id: string; nearest_machine: string; distance_m: number; status: string }[]
  canvas: { width: number; height: number }; as_of: string
}

const ZONE_COLORS: Record<string, { border: string; fill: string; label: string }> = {
  EXCAVATION:  { border: '#f59e0b', fill: 'rgba(245,158,11,0.08)',  label: '#f59e0b' },
  LOADING_BAY: { border: '#f59e0b', fill: 'rgba(245,158,11,0.06)',  label: '#f59e0b' },
  RESTRICTED:  { border: '#ef4444', fill: 'rgba(239,68,68,0.10)',   label: '#ef4444' },
  HAUL_ROAD:   { border: '#64748b', fill: 'rgba(100,116,139,0.08)', label: '#64748b' },
  DUMP_ZONE:   { border: '#8b5cf6', fill: 'rgba(139,92,246,0.08)',  label: '#8b5cf6' },
  SAFE_AREA:   { border: '#4ade80', fill: 'rgba(74,222,128,0.10)',  label: '#4ade80' },
  WORKSHOP:    { border: '#60a5fa', fill: 'rgba(96,165,250,0.08)',  label: '#60a5fa' },
  FUEL_STATION:{ border: '#fb923c', fill: 'rgba(251,146,60,0.08)',  label: '#fb923c' },
}

export default function SiteMapPage() {
  const { alerts } = useAlertStore()
  const [simulating, setSimulating] = useState(false)
  const [simulatedWorker, setSimulatedWorker] = useState<Worker | null>(null)
  const [alertFlash, setAlertFlash] = useState(false)
  const svgRef = useRef<SVGSVGElement>(null)

  const { data, isLoading, refetch } = useQuery<SiteMapData>({
    queryKey: ['sitemap'],
    queryFn: async () => {
      const res = await fetch(`${BASE}/sitemap`, { headers: authHeaders() })
      const j = await res.json()
      return j.data
    },
    refetchInterval: 5000,
  })

  // Listen for SITE_MAP_UPDATE from WebSocket
  useEffect(() => {
    const latestAlert = alerts[0]
    if (latestAlert && latestAlert.alert_type?.includes('PROXIMITY')) {
      setAlertFlash(true)
      setTimeout(() => setAlertFlash(false), 2000)
    }
  }, [alerts])

  async function handleSimulateApproach() {
    setSimulating(true)
    try {
      const res = await fetch(`${BASE}/sitemap/simulate-approach`, {
        method: 'POST', headers: authHeaders(),
      })
      const j = await res.json()
      if (j.data?.worker) {
        setSimulatedWorker(j.data.worker)
        setAlertFlash(true)
        setTimeout(() => setAlertFlash(false), 3000)
      }
      refetch()
    } finally {
      setSimulating(false)
    }
  }

  const canvas = data?.canvas ?? { width: 1000, height: 700 }
  const machines = data?.machines ?? []
  const workers = [...(data?.workers ?? []), ...(simulatedWorker ? [simulatedWorker] : [])]
  const zones = data?.zones ?? []
  const proximityAlerts = data?.proximity_alerts ?? []

  // Scale SVG to fit container
  const viewBox = `0 0 ${canvas.width} ${canvas.height}`

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Live Site Map"
        subtitle="Real-time bird's-eye view with proximity detection and zone monitoring"
        icon={<MapPin size={20} />}
        actions={
          <div className="flex gap-2 items-center">
            {alertFlash && (
              <span className="text-xs text-red-400 animate-pulse font-semibold flex items-center gap-1">
                <AlertTriangle size={12} /> PROXIMITY ALERT
              </span>
            )}
            <button
              onClick={() => refetch()}
              className="btn-secondary text-xs flex items-center gap-1.5"
              aria-label="Refresh site map"
            >
              <RefreshCw size={12} />
              Refresh
            </button>
            <button
              onClick={handleSimulateApproach}
              disabled={simulating}
              className="btn-primary text-xs flex items-center gap-1.5 disabled:opacity-50"
              aria-label="Simulate worker approaching machine"
            >
              <Play size={12} />
              {simulating ? 'Simulating…' : 'Simulate Worker Approach'}
            </button>
          </div>
        }
      />

      <div className="flex-1 overflow-hidden flex gap-4 p-6">
        {/* SVG Map */}
        <div className="flex-1 bg-slate-800 rounded-xl border border-slate-700 overflow-hidden relative">
          {isLoading ? (
            <div className="flex items-center justify-center h-full text-slate-400 text-sm">Loading site map…</div>
          ) : (
            <svg
              ref={svgRef}
              viewBox={viewBox}
              className="w-full h-full"
              style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)' }}
              aria-label="Live site map"
            >
              {/* Grid */}
              <defs>
                <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                  <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#1e293b" strokeWidth="1" />
                </pattern>
              </defs>
              <rect width={canvas.width} height={canvas.height} fill="url(#grid)" />

              {/* Zones */}
              {zones.map((z) => {
                const style = ZONE_COLORS[z.type] ?? ZONE_COLORS['SAFE_AREA']
                return (
                  <g key={z.id}>
                    <rect
                      x={z.x} y={z.y} width={z.w} height={z.h}
                      fill={style.fill}
                      stroke={style.border}
                      strokeWidth="1.5"
                      strokeDasharray={z.type === 'RESTRICTED' ? '6,4' : 'none'}
                      rx="4"
                    />
                    <text
                      x={z.x + 8} y={z.y + 16}
                      fill={style.label}
                      fontSize="11"
                      fontWeight="500"
                    >
                      {z.label}
                    </text>
                  </g>
                )
              })}

              {/* Machine proximity radii */}
              {machines.filter((m) => m.status === 'ACTIVE').map((m) => (
                <g key={`radius-${m.machine_id}`}>
                  <circle
                    cx={m.x} cy={m.y}
                    r={m.proximity_warning_radius_px}
                    fill="rgba(245,158,11,0.04)"
                    stroke="rgba(245,158,11,0.25)"
                    strokeWidth="1"
                    strokeDasharray="4,4"
                  />
                  <circle
                    cx={m.x} cy={m.y}
                    r={m.proximity_critical_radius_px}
                    fill="rgba(239,68,68,0.06)"
                    stroke="rgba(239,68,68,0.35)"
                    strokeWidth="1"
                    strokeDasharray="3,3"
                  />
                </g>
              ))}

              {/* Machines */}
              {machines.map((m) => {
                const isActive = m.status === 'ACTIVE'
                const inAlert = alertFlash && simulatedWorker?.nearest_machine === m.machine_code
                const color = inAlert ? '#ef4444' : isActive ? '#4ade80' : m.status === 'MAINTENANCE' ? '#f59e0b' : '#64748b'
                return (
                  <g key={m.machine_id}>
                    {/* Pulse animation for alerted machine */}
                    {inAlert && (
                      <circle cx={m.x} cy={m.y} r="28" fill="none" stroke="#ef4444" strokeWidth="2" opacity="0.5">
                        <animate attributeName="r" from="20" to="40" dur="1s" repeatCount="indefinite" />
                        <animate attributeName="opacity" from="0.8" to="0" dur="1s" repeatCount="indefinite" />
                      </circle>
                    )}
                    <rect
                      x={m.x - 16} y={m.y - 14}
                      width="32" height="28"
                      fill={`${color}22`}
                      stroke={color}
                      strokeWidth="2"
                      rx="3"
                    />
                    <text x={m.x} y={m.y - 1} textAnchor="middle" fill={color} fontSize="9" fontWeight="bold">
                      {m.machine_type.slice(0, 3)}
                    </text>
                    <text x={m.x} y={m.y + 9} textAnchor="middle" fill={color} fontSize="8">
                      {m.machine_code}
                    </text>
                    {/* Operator dot */}
                    {m.current_operator_name && (
                      <circle cx={m.x + 10} cy={m.y - 10} r="4" fill="#60a5fa" stroke="#1e293b" strokeWidth="1" />
                    )}
                    {/* Machine code label below */}
                    <text x={m.x} y={m.y + 26} textAnchor="middle" fill={color} fontSize="7" opacity="0.7">
                      {m.health_score ? `${m.health_score.toFixed(0)}%` : ''}
                    </text>
                  </g>
                )
              })}

              {/* Workers */}
              {workers.map((w) => {
                const isCritical = w.proximity_status === 'CRITICAL'
                const isWarning = w.proximity_status === 'WARNING'
                const color = isCritical ? '#ef4444' : isWarning ? '#f59e0b' : '#f1f5f9'
                return (
                  <g key={w.worker_id}>
                    <circle
                      cx={w.x} cy={w.y} r={isCritical ? 6 : 4}
                      fill={isCritical ? '#ef4444' : isWarning ? '#f59e0b' : '#f1f5f9'}
                      stroke={isCritical ? '#fee2e2' : '#334155'}
                      strokeWidth="1.5"
                    >
                      {isCritical && (
                        <animate attributeName="opacity" values="1;0.3;1" dur="0.7s" repeatCount="indefinite" />
                      )}
                    </circle>
                    {(isCritical || isWarning) && (
                      <text x={w.x + 7} y={w.y + 4} fill={color} fontSize="8" fontWeight="600">
                        {w.distance_m?.toFixed(1)}m
                      </text>
                    )}
                  </g>
                )
              })}
            </svg>
          )}
        </div>

        {/* Legend panel */}
        <div className="w-56 flex flex-col gap-4 flex-shrink-0">
          {/* Proximity alerts */}
          {(proximityAlerts.length > 0 || simulatedWorker) && (
            <div className="card border border-red-700/50 bg-red-900/20">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={14} className="text-red-400" />
                <span className="text-xs font-semibold text-red-400">Proximity Alerts</span>
              </div>
              {simulatedWorker && (
                <div className="text-xs text-red-300 mb-1">
                  Simulated worker {simulatedWorker.distance_m?.toFixed(1)}m from {simulatedWorker.nearest_machine}
                  <span className="ml-1 text-red-400 font-bold">CRITICAL</span>
                </div>
              )}
              {proximityAlerts.map((a) => (
                <div key={a.worker_id} className="text-xs text-red-300">
                  Worker near {a.nearest_machine}: {a.distance_m?.toFixed(1)}m
                </div>
              ))}
            </div>
          )}

          {/* Machine status */}
          <div className="card">
            <div className="flex items-center gap-2 mb-3">
              <Truck size={14} className="text-amber-400" />
              <span className="text-xs font-semibold text-slate-300">Machines ({machines.length})</span>
            </div>
            <div className="space-y-2">
              {machines.map((m) => (
                <div key={m.machine_id} className="flex items-center justify-between text-xs">
                  <span className="text-amber-400 font-mono">{m.machine_code}</span>
                  <StatusDot
                    status={m.status === 'ACTIVE' ? 'green' : m.status === 'MAINTENANCE' ? 'amber' : 'gray'}
                    label={m.status}
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Legend */}
          <div className="card">
            <div className="text-xs font-semibold text-slate-300 mb-3">Legend</div>
            <div className="space-y-2 text-xs text-slate-400">
              {Object.entries(ZONE_COLORS).slice(0, 6).map(([type, style]) => (
                <div key={type} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-sm border" style={{ borderColor: style.border, background: style.fill }} />
                  <span>{type.replace('_', ' ')}</span>
                </div>
              ))}
              <div className="border-t border-slate-700 pt-2 mt-2 space-y-1">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-400" />
                  <span>Active machine</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-white" />
                  <span>Worker (safe)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <span>Worker (critical)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-400" />
                  <span>Operator in cab</span>
                </div>
              </div>
            </div>
          </div>

          {/* Radii legend */}
          <div className="card text-xs text-slate-400 space-y-1">
            <div className="text-slate-300 font-semibold mb-2">Proximity Zones</div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-px" style={{ border: '1px dashed rgba(245,158,11,0.6)' }} />
              <span>Warning (10m)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-px" style={{ border: '1px dashed rgba(239,68,68,0.6)' }} />
              <span>Critical (5m)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
