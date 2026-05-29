import { cn } from '@/lib/utils'

function Spinner({ className }) {
  return (
    <div
      className={cn(
        'h-4 w-4 animate-spin rounded-full border-2 border-slate-200 border-t-slate-600',
        className
      )}
    />
  )
}

export default Spinner
