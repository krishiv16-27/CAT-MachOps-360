interface StatusDotProps {
  status: 'green' | 'amber' | 'red' | 'blue' | 'gray'
  pulse?: boolean
  size?: 'sm' | 'md' | 'lg'
  label?: string
}

const COLOR_MAP = {
  green: 'bg-green-400',
  amber: 'bg-amber-400',
  red: 'bg-red-400',
  blue: 'bg-blue-400',
  gray: 'bg-slate-500',
}

const SIZE_MAP = {
  sm: 'w-1.5 h-1.5',
  md: 'w-2 h-2',
  lg: 'w-3 h-3',
}

export default function StatusDot({ status, pulse = false, size = 'md', label }: StatusDotProps) {
  return (
    <span className="inline-flex items-center gap-1.5" role="status" aria-label={label ?? status}>
      <span className="relative inline-flex">
        <span className={`${SIZE_MAP[size]} rounded-full ${COLOR_MAP[status]}`} />
        {pulse && (
          <span className={`absolute inset-0 rounded-full ${COLOR_MAP[status]} animate-ping opacity-75`} />
        )}
      </span>
      {label && <span className="text-xs text-slate-400">{label}</span>}
    </span>
  )
}
