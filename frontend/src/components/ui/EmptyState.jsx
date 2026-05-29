function EmptyState({ title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-10 text-center">
      <p className="text-sm text-slate-500">{title}</p>
      {description && (
        <p className="text-xs text-slate-400">{description}</p>
      )}
      {action && <div className="mt-1">{action}</div>}
    </div>
  )
}

export default EmptyState
