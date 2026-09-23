type Severity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | string

const CLASSES: Record<string, string> = {
  CRITICAL: 'badge-critical',
  HIGH: 'bg-orange-900/50 text-orange-400 border border-orange-800 text-xs font-medium px-2 py-0.5 rounded-full',
  MEDIUM: 'badge-medium',
  LOW: 'badge-low',
}

export default function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={CLASSES[severity?.toUpperCase()] ?? 'badge-low'}>
      {severity}
    </span>
  )
}
