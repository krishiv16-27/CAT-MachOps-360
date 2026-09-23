/**
 * ExplainThis — a small "?" button that opens a popover explaining
 * exactly which factors contributed to a score and by how much.
 * No new API needed — accepts component breakdown as props.
 */
import { useState, useRef, useEffect } from 'react'
import { HelpCircle, X } from 'lucide-react'

export interface ScoreComponent {
  label: string
  score?: number
  weight?: number
  value?: string | number
  detail?: string
  color?: 'green' | 'amber' | 'red' | 'blue'
}

interface ExplainThisProps {
  title: string
  summary?: string
  components: ScoreComponent[]
  disclaimer?: string
  /** Position: 'left' opens to the left, 'right' (default) opens to the right */
  position?: 'left' | 'right' | 'above'
}

function componentColor(score?: number): string {
  if (score === undefined) return 'text-slate-400'
  if (score >= 90) return 'text-green-400'
  if (score >= 75) return 'text-amber-400'
  return 'text-red-400'
}

function barColor(score?: number): string {
  if (score === undefined) return 'bg-slate-600'
  if (score >= 90) return 'bg-green-500'
  if (score >= 75) return 'bg-amber-500'
  return 'bg-red-500'
}

export default function ExplainThis({
  title,
  summary,
  components,
  disclaimer,
  position = 'right',
}: ExplainThisProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  // Close on outside click
  useEffect(() => {
    function handle(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    if (open) document.addEventListener('mousedown', handle)
    return () => document.removeEventListener('mousedown', handle)
  }, [open])

  const posClass =
    position === 'left' ? 'right-0' :
    position === 'above' ? 'bottom-8 left-0' :
    'left-0'

  return (
    <div className="relative inline-block" ref={ref}>
      <button
        onClick={(e) => { e.stopPropagation(); setOpen(!open) }}
        className="text-slate-500 hover:text-amber-400 transition-colors ml-1 align-middle"
        aria-label={`Explain ${title} score`}
        title={`Explain this: ${title}`}
      >
        <HelpCircle size={13} />
      </button>

      {open && (
        <div
          className={`absolute ${posClass} z-50 w-72 bg-slate-800 border border-slate-600 rounded-xl shadow-2xl p-4`}
          style={{ top: position === 'above' ? undefined : '100%', marginTop: position === 'above' ? undefined : '4px' }}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-amber-400 uppercase tracking-wide">{title}</span>
            <button
              onClick={() => setOpen(false)}
              className="text-slate-500 hover:text-slate-300"
              aria-label="Close explanation"
            >
              <X size={12} />
            </button>
          </div>

          {summary && (
            <p className="text-xs text-slate-400 mb-3 leading-relaxed">{summary}</p>
          )}

          {/* Components */}
          <div className="space-y-2">
            {components.map((c, i) => (
              <div key={i}>
                <div className="flex items-center justify-between mb-0.5">
                  <span className="text-xs text-slate-300">{c.label}</span>
                  <div className="flex items-center gap-1.5">
                    {c.weight !== undefined && (
                      <span className="text-xs text-slate-500">{Math.round(c.weight * 100)}%</span>
                    )}
                    {c.score !== undefined ? (
                      <span className={`text-xs font-bold ${componentColor(c.score)}`}>
                        {c.score.toFixed(0)}%
                      </span>
                    ) : c.value !== undefined ? (
                      <span className="text-xs font-bold text-slate-200">{c.value}</span>
                    ) : null}
                  </div>
                </div>
                {c.score !== undefined && (
                  <div className="w-full bg-slate-700 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full ${barColor(c.score)}`}
                      style={{ width: `${Math.min(c.score, 100)}%` }}
                    />
                  </div>
                )}
                {c.detail && (
                  <p className="text-xs text-slate-500 mt-0.5">{c.detail}</p>
                )}
              </div>
            ))}
          </div>

          {disclaimer && (
            <p className="text-xs text-slate-600 mt-3 pt-2 border-t border-slate-700 leading-relaxed">
              {disclaimer}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
