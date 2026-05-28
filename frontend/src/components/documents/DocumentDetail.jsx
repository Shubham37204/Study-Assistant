// src/components/documents/DocumentDetail.jsx
// Appears on hover — shows summary and topics extracted during ingestion

function DocumentDetail({ doc }) {
  return (
    <div className="absolute left-full top-0 z-20 ml-2 w-64 rounded-xl border border-slate-200 bg-white p-4 shadow-lg">
      <p className="mb-2 text-xs font-semibold text-slate-700">Summary</p>
      <p className="mb-3 line-clamp-4 text-xs leading-relaxed text-slate-500">
        {doc.summary}
      </p>

      {doc.key_topics?.length > 0 && (
        <>
          <p className="mb-1.5 text-xs font-semibold text-slate-700">Topics</p>
          <div className="flex flex-wrap gap-1">
            {doc.key_topics.slice(0, 6).map((topic) => (
              <span
                key={topic}
                className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600"
              >
                {topic}
              </span>
            ))}
          </div>
        </>
      )}

      <p className="mt-3 text-xs text-slate-400">
        {doc.total_chunks} chunk{doc.total_chunks !== 1 ? 's' : ''} indexed
      </p>
    </div>
  )
}

export default DocumentDetail
