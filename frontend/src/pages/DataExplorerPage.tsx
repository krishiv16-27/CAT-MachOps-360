/**
 * Data Explorer — browse all generated CSV datasets as interactive tables.
 * Colour-coded cells, download buttons, summary stats.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Database, Download, RefreshCw, TrendingUp, AlertTriangle, Leaf, Shield } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import { useAuthStore } from '../store/authStore'

const BASE = '/api/v1'
function authHeaders() {
  const token = useAuthStore.getState().token ?? ''
  return { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
}
async function fetchDataset(name: string) {
  const res = await fetch(`${BASE}/data-explorer/${name}`, { headers: authHeaders() })
  const j = await res.json()
  return j.data as { rows: Record<string, string>[]; summary: Record<string, unknown>; dataset: string }
}

const TABS = [
  { id: 'operators_profile', label: 'Operators', icon: Shield, description: 'Digital twin snapshot per operator' },
  { id: 'machine_health_snapshot', label: 'Machines', icon: TrendingUp, description: 'Machine health breakdown' },
  { id: 'telemetry_correlated', label: 'Telemetry', icon: TrendingUp, description: '120 rows/machine, correlated time-series' },
  { id: 'safety_events_enriched', label: 'Safety Events', icon: AlertTriangle, description: 'Enriched alert history' },
  { id: 'task_performance', label: 'Tasks', icon: Database, description: 'Task outcomes with ETA accuracy' },
  { id: 'carbon_passport', label: 'Carbon Passport', icon: Leaf, description: 'Per-operator CO₂ savings' },
  { id: 'near_miss_log', label: 'Near Misses', icon: AlertTriangle, description: 'Self-corrected near-miss events' },
  { id: 'operator_machine_pairing', label: 'Compatibility', icon: Shield, description: 'Operator-machine compatibility matrix' },
]

// Colour coding rules per column
function cellClass(col: string, val: string): string {
  const num = parseFloat(val)
  if (col === 'anomaly_label') return val === 'UNUSUAL' ? 'text-red-400 font-semibold' : 'text-green-400'
  if (col === 'certification_valid') return val === 'NO' ? 'text-red-400 font-bold' : 'text-green-400'
  if (col === 'was_self_corrected' || col === 'was_self_corrected_before_alert')
    return val === 'YES' ? 'text-green-400 font-semibold' : 'text-slate-400'
  if (col === 'recommended') return val === 'NO' ? 'text-red-400' : 'text-green-400'
  if (col === 'status') {
    if (val === 'MAINTENANCE') return 'text-amber-400'
    if (val === 'ACTIVE') return 'text-green-400'
    return 'text-slate-400'
  }
  if (col === 'predicted_maintenance_risk') {
    if (val === 'HIGH') return 'text-red-400 font-semibold'
    if (val === 'MEDIUM') return 'text-amber-400'
    return 'text-green-400'
  }
  if (col === 'label' || col === 'carbon_rating') {
    if (val === 'EXCELLENT') return 'text-green-400'
    if (val === 'SUITABLE' || val === 'GOOD') return 'text-blue-400'
    if (val === 'NOT RECOMMENDED' || val === 'BELOW_AVERAGE') return 'text-red-400'
    return 'text-amber-400'
  }
  if (col === 'severity') {
    if (val === 'CRITICAL') return 'text-red-500 font-bold'
    if (val === 'HIGH') return 'text-orange-400'
    if (val === 'MEDIUM') return 'text-amber-400'
    return 'text-slate-400'
  }
  if (col === 'anomaly_flag') return val === 'YES' ? 'text-red-400 font-semibold' : 'text-slate-400'
  if (!isNaN(num) && val !== '') {
    if (col.includes('health') || col.includes('score') || col.includes('pct') || col.includes('pct')) {
      if (num >= 90) return 'text-green-400'
      if (num >= 75) return 'text-amber-400'
      if (num < 60) return 'text-red-400'
    }
    if (col.includes('co2') || col.includes('carbon') || col.includes('saved')) {
      if (num > 0) return 'text-green-400'
      if (num < 0) return 'text-red-400'
    }
  }
  return ''
}

function SummaryBar({ summary }: { summary: Record<string, unknown> }) {
  const items = Object.entries(summary).filter(([k]) => k !== 'total_rows')
  return (
    <div className="flex flex-wrap gap-4 text-xs text-slate-400 mb-3 border-b border-slate-700 pb-3">
      <span className="text-slate-300 font-semibold">{summary.total_rows as number} rows</span>
      {items.map(([k, v]) => (
        <span key={k} className="text-slate-400">
          {k.replace(/_/g, ' ')}: <span className="text-amber-400 font-medium">{String(v)}</span>
        </span>
      ))}
    </div>
  )
}

export default function DataExplorerPage() {
  const [activeTab, setActiveTab] = useState(TABS[0].id)
  const [search, setSearch] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['data-explorer', activeTab, refreshKey],
    queryFn: () => fetchDataset(activeTab),
  })

  const rows = data?.rows ?? []
  const summary = data?.summary ?? {}

  const filtered = search
    ? rows.filter((r) => Object.values(r).some((v) => String(v).toLowerCase().includes(search.toLowerCase())))
    : rows

  const cols = rows.length > 0 ? Object.keys(rows[0]) : []

  async function handleDownload() {
    const token = useAuthStore.getState().token ?? ''
    const res = await fetch(`${BASE}/data-explorer/${activeTab}/download`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${activeTab}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  async function handleRegenerate() {
    const token = useAuthStore.getState().token ?? ''
    await fetch(`${BASE}/data-explorer/regenerate`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } })
    setRefreshKey((k) => k + 1)
  }

  const currentTab = TABS.find((t) => t.id === activeTab)

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        title="Data Explorer"
        subtitle="Browse all generated datasets — story-driven, correlated, judge-readable"
        icon={<Database size={20} />}
        actions={
          <div className="flex gap-2">
            <button
              onClick={handleRegenerate}
              className="btn-secondary text-xs flex items-center gap-1.5"
              aria-label="Regenerate all datasets"
            >
              <RefreshCw size={12} />
              Regenerate
            </button>
            <button
              onClick={handleDownload}
              className="btn-primary text-xs flex items-center gap-1.5"
              aria-label={`Download ${activeTab} CSV`}
            >
              <Download size={12} />
              Download CSV
            </button>
          </div>
        }
      />

      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Tab bar */}
        <div className="flex gap-1 px-6 pt-4 border-b border-slate-700 overflow-x-auto flex-shrink-0">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setSearch('') }}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs rounded-t-lg whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'bg-slate-800 text-amber-400 border-b-2 border-amber-400'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              aria-label={`Show ${tab.label} dataset`}
            >
              <tab.icon size={12} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="card">
            {/* Description + search */}
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs text-slate-400">{currentTab?.description}</p>
              <input
                type="text"
                placeholder="Search rows..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="bg-slate-700 text-slate-200 text-xs px-3 py-1.5 rounded border border-slate-600 w-48 focus:outline-none focus:border-amber-500"
                aria-label="Search table rows"
              />
            </div>

            {Object.keys(summary).length > 0 && <SummaryBar summary={summary} />}

            {isLoading ? (
              <div className="text-center py-12 text-slate-400 text-sm animate-pulse">Loading dataset…</div>
            ) : filtered.length === 0 ? (
              <div className="text-center py-12 text-slate-500 text-sm">
                No data found. Run "Regenerate" to generate CSV files.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-slate-700">
                      {cols.map((c) => (
                        <th key={c} className="text-left py-2 pr-3 text-slate-500 font-medium whitespace-nowrap">
                          {c.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {filtered.slice(0, 200).map((row, i) => (
                      <tr key={i} className="hover:bg-slate-800/40 transition-colors">
                        {cols.map((c) => (
                          <td key={c} className={`py-1.5 pr-3 whitespace-nowrap ${cellClass(c, row[c] ?? '')}`}>
                            {row[c] ?? '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filtered.length > 200 && (
                  <p className="text-xs text-slate-500 mt-2 text-center">
                    Showing 200 of {filtered.length} rows. Use search to filter.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
