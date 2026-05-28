// src/components/chat/CitationList.jsx
import { useState } from 'react'
import CitationCard from './CitationCard'

function CitationList({ citations }) {
  const [open, setOpen] = useState(false)

  if (!citations?.length) return null

  return (
    <div className="mt-3 border-t border-slate-100 pt-3">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-1.5 text-xs text-slate-400 transition-colors hover:text-slate-600"
      >
        <span>
          {citations.length} source{citations.length > 1 ? 's' : ''}
        </span>
        <span>{open ? '↑' : '↓'}</span>
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          {citations.map((c, i) => (
            <CitationCard key={c.chunk_id ?? i} citation={c} index={i} />
          ))}
        </div>
      )}
    </div>
  )
}

export default CitationList
