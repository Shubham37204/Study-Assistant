import { cn } from '@/lib/utils'

const styles = {
  factual:   'bg-blue-50 text-blue-600',
  explain:   'bg-green-50 text-green-600',
  summarize: 'bg-amber-50 text-amber-700',
  compare:   'bg-purple-50 text-purple-600',
  greeting:  'bg-slate-100 text-slate-500',
}

function IntentBadge({ intent }) {
  if (!intent) return null

  return (
    <span
      className={cn(
        'rounded-full px-2 py-0.5 text-xs font-medium',
        styles[intent] ?? 'bg-slate-100 text-slate-500'
      )}
    >
      {intent}
    </span>
  )
}

export default IntentBadge