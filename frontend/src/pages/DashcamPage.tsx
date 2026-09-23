import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Camera, Zap } from 'lucide-react'
import { cvApi, machinesApi } from '../services/api'
import PageHeader from '../components/ui/PageHeader'
import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'

export default function DashcamPage() {
  const [selectedMachine, setSelectedMachine] = useState('')
  const qc = useQueryClient()

  const { data: cameras } = useQuery({ queryKey: ['cameras'], queryFn: cvApi.cameras })
  const { data: events, isLoading } = useQuery({
    queryKey: ['cv-events'],
    queryFn: cvApi.events,
    refetchInterval: 10_000,
  })
  const { data: machines } = useQuery({ queryKey: ['machines'], queryFn: () => machinesApi.list() })

  const simMutation = useMutation({
    mutationFn: (type: string) => cvApi.simulate(type, selectedMachine || (machines?.[0]?.machine_id ?? ''), 3.8),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['cv-events'] }),
  })

  const eventsArray = events as Record<string, unknown>[] | undefined

  return (
    <div className="flex flex-col h-full">
      <PageHeader title="Dashcam & CV" subtitle="Simulated computer vision event monitoring" icon={<Camera size={20} />} />
      <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Camera feeds (simulated) */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-slate-300">Camera Feeds (Simulated)</h3>
          <div className="grid grid-cols-2 gap-3">
            {(cameras as Record<string, unknown>[] | undefined)?.slice(0, 4).map((cam) => (
              <div key={cam.camera_id as string} className="card aspect-video flex flex-col items-center justify-center bg-slate-700/50">
                <div className="relative w-full h-full flex flex-col items-center justify-center p-3">
                  <div className="w-full aspect-video bg-slate-900 rounded-lg flex items-center justify-center mb-2 relative overflow-hidden">
                    {/* Simulated camera overlay */}
                    <div className="absolute inset-0 bg-gradient-to-br from-slate-800 to-slate-900" />
                    <div className="absolute top-1 left-1 flex items-center gap-1">
                      <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                      <span className="text-xs text-red-400 font-mono">REC</span>
                    </div>
                    <Camera size={20} className="text-slate-600 relative z-10" />
                  </div>
                  <div className="text-xs text-amber-400 font-mono">{cam.camera_id as string}</div>
                  <div className="text-xs text-green-400">{cam.status as string}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Simulate events */}
          <div className="card">
            <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
              <Zap size={14} className="text-amber-400" />
              Demo: Simulate CV Event
            </h3>
            <div className="mb-3">
              <select
                value={selectedMachine}
                onChange={(e) => setSelectedMachine(e.target.value)}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500 mb-2"
                aria-label="Select machine for simulation"
              >
                <option value="">Select machine…</option>
                {machines?.filter((m) => m.status === 'ACTIVE').map((m) => (
                  <option key={m.machine_id} value={m.machine_id}>{m.machine_code}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              {[
                { type: 'person_detected', label: '👤 Person Detected', color: 'bg-red-600 hover:bg-red-500' },
                { type: 'vehicle_detected', label: '🚛 Vehicle Near', color: 'bg-orange-600 hover:bg-orange-500' },
                { type: 'obstacle_detected', label: '⚠ Obstacle', color: 'bg-yellow-600 hover:bg-yellow-500' },
                { type: 'restricted_zone_entry', label: '🚫 Zone Entry', color: 'bg-red-800 hover:bg-red-700' },
              ].map(({ type, label, color }) => (
                <button
                  key={type}
                  onClick={() => simMutation.mutate(type)}
                  disabled={simMutation.isPending}
                  className={`${color} text-white text-xs px-3 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50`}
                  aria-label={`Simulate ${label} CV event`}
                >
                  {label}
                </button>
              ))}
            </div>
            {simMutation.isSuccess && (
              <p className="text-xs text-green-400 mt-2">✓ Event simulated — check alerts feed</p>
            )}
          </div>
        </div>

        {/* Recent CV events */}
        <div>
          <h3 className="text-sm font-semibold text-slate-300 mb-3">Recent CV Events</h3>
          {isLoading && <div className="text-slate-400 text-sm animate-pulse">Loading events…</div>}
          <div className="space-y-2">
            {eventsArray?.length === 0 && <p className="text-slate-500 text-sm text-center py-8">No CV events recorded</p>}
            {eventsArray?.map((e) => (
              <div key={e.event_id as string} className={`p-3 rounded-lg border text-sm ${
                e.person_detected ? 'border-red-800/50 bg-red-900/10' :
                e.vehicle_detected ? 'border-orange-800/50 bg-orange-900/10' :
                'border-slate-700 bg-slate-700/20'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-slate-200 text-xs">{e.event_type as string}</span>
                    <div className="flex gap-2 mt-1">
                      {e.person_detected && <span className="text-xs text-red-400">👤 Person</span>}
                      {e.vehicle_detected && <span className="text-xs text-orange-400">🚛 Vehicle</span>}
                      {e.obstacle_detected && <span className="text-xs text-yellow-400">⚠ Obstacle</span>}
                      {e.restricted_zone_entry && <span className="text-xs text-red-400">🚫 Zone</span>}
                      {e.estimated_distance_m && (
                        <span className={`text-xs ${(e.estimated_distance_m as number) < 5 ? 'text-red-400' : 'text-slate-400'}`}>
                          {(e.estimated_distance_m as number).toFixed(1)}m
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 text-right">
                    <div className="font-mono">{e.camera_id as string}</div>
                    <div>{formatDistanceToNow(new Date(e.timestamp as string), { addSuffix: true })}</div>
                    <div className="text-slate-600">conf: {((e.confidence as number) * 100).toFixed(0)}%</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
