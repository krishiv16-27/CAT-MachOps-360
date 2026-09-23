import type { ReactNode } from 'react'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface KpiCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: ReactNode
  severity?: 'success' | 'warning' | 'danger' | 'info' | 'neutral'
  trend?: string
  trendDir?: 'up' | 'down' | 'flat'
  onClick?: () => void
  loading?: boolean
  badge?: string
}

const SEVERITY_STYLES = {
  success: 'border-green-800/50 hover:border-green-600/50',
  warning: 'border-yellow-800/50 hover:border-yellow-600/50',
  danger: 'border-red-800/50 hover:border-red-600/50',
  info: 'border-blue-800/50 hover:border-blue-600/50',
  neutral: 'border-slate-700 hover:border-slate-500',
}

const ICON_STYLES = {
  success: 'text-green-400 bg-green-900/30',
  warning: 'text-yellow-400 bg-yellow-900/30',
  danger: 'text-red-400 bg-red-900/30',
  info: 'text-blue-400 bg-blue-900/30',
  neutral: 'text-slate-400 bg-slate-700/50',
}

const TREND_COLOR = {
  up: 'text-green-400',
  down: 'text-red-400',
  flat: 'text-slate-400',
}

export default function KpiCard({
  title,
  value,
  subtitle,
  icon,
  severity = 'neutral',
  trend,
  trendDir = 'flat',
  onClick,
  loading = false,
  badge,
}: KpiCardProps) {
  const isClickable = !!onClick

  return (
    <button
      onClick={onClick}
      disabled={!isClickable}
      aria-label={`${title}: ${value}${subtitle ? ` — ${subtitle}` : ''}. ${isClickable ? 'Click to view details.' : ''}`}
      className={`
        bg-slate-800 border rounded-xl p-4 text-left transition-all duration-200 w-full
        ${SEVERITY_STYLES[severity]}
        ${isClickable ? 'cursor-pointer hover:bg-slate-750 hover:shadow-lg hover:shadow-black/20 active:scale-[0.98]' : 'cursor-default'}
      `}
    >
      {loading ? (
        <div className="animate-pulse space-y-2">
          <div className="h-3 bg-slate-700 rounded w-2/3" />
          <div className="h-7 bg-slate-700 rounded w-1/2" />
        </div>
      ) : (
        <>
          <div className="flex items-start justify-between mb-3">
            <div className={`p-2 rounded-lg ${ICON_STYLES[severity]}`}>
              {icon}
            </div>
            {badge && (
              <span className="text-xs bg-slate-700 text-slate-400 px-2 py-0.5 rounded-full">
                {badge}
              </span>
            )}
          </div>
          <div className="text-2xl font-bold text-slate-100 mb-0.5">{value}</div>
          <div className="text-xs text-slate-400 font-medium uppercase tracking-wide">{title}</div>
          {(subtitle || trend) && (
            <div className="flex items-center gap-2 mt-2">
              {subtitle && <span className="text-xs text-slate-500">{subtitle}</span>}
              {trend && (
                <span className={`flex items-center gap-0.5 text-xs ${TREND_COLOR[trendDir]}`}>
                  {trendDir === 'up' && <TrendingUp size={10} />}
                  {trendDir === 'down' && <TrendingDown size={10} />}
                  {trendDir === 'flat' && <Minus size={10} />}
                  {trend}
                </span>
              )}
            </div>
          )}
          {isClickable && (
            <div className="mt-2 text-xs text-slate-600 hover:text-amber-400 transition-colors">
              Click to view details →
            </div>
          )}
        </>
      )}
    </button>
  )
}
