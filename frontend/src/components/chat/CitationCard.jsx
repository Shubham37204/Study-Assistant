// src/components/chat/CitationCard.jsx
function CitationCard({ citation, index }) {
  return (
    <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
      <div className="mb-1.5 flex items-center justify-between">
        <span className="text-xs font-medium text-slate-500">
          Source {index + 1}
        </span>
        {citation.page_number && (
          <span className="text-xs text-slate-400">p. {citation.page_number}</span>
        )}
      </div>
      <p className="line-clamp-3 text-xs leading-relaxed text-slate-500">
        {citation.excerpt}
      </p>
    </div>
  )
}

export default CitationCard