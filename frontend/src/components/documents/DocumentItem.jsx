import { useState } from 'react'
import { cn } from '@/lib/utils'
import useAppStore from '@/store/useAppStore'
import { useDeleteDocument } from '@/hooks/useDeleteDocument'
import DocumentDetail from './DocumentDetail'

const typeColors = {
  pdf:      'bg-red-50 text-red-600',
  text:     'bg-blue-50 text-blue-600',
  markdown: 'bg-slate-100 text-slate-600',
  image:    'bg-green-50 text-green-600',
  url:      'bg-purple-50 text-purple-600',
}

function DocumentItem({ doc }) {
  const { selectedDocIds, toggleDocSelection } = useAppStore()
  const [hovered, setHovered] = useState(false)
  const { mutate: remove, isPending: deleting } = useDeleteDocument()
  const isSelected = selectedDocIds.includes(doc.document_id)

  function handleDelete(e) {
    e.stopPropagation()
    remove(doc.document_id)
  }

  return (
    <div
      role="button"
      onClick={() => toggleDocSelection(doc.document_id)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={cn(
        'relative flex cursor-pointer items-start gap-2.5 rounded-lg border p-3 transition-colors',
        isSelected ? 'border-slate-300 bg-white' : 'border-slate-100 bg-white hover:border-slate-200',
        deleting && 'opacity-40 pointer-events-none'
      )}
    >
      <input
        type="checkbox"
        checked={isSelected}
        onChange={() => toggleDocSelection(doc.document_id)}
        onClick={(e) => e.stopPropagation()}
        className="mt-0.5 h-3.5 w-3.5 shrink-0 cursor-pointer accent-slate-800"
      />

      <div className="min-w-0 flex-1">
        <p title={doc.file_name} className="truncate text-xs font-medium text-slate-700">
          {doc.file_name}
        </p>
        <div className="mt-1.5 flex items-center gap-2">
          <span className={cn('rounded px-1.5 py-0.5 text-xs font-medium', typeColors[doc.file_type] ?? 'bg-slate-100 text-slate-500')}>
            {doc.file_type}
          </span>
          <span className="text-xs text-slate-400">{doc.total_chunks} chunks</span>
        </div>
      </div>

      {hovered && !deleting && (
        <button
          onClick={handleDelete}
          className="shrink-0 rounded p-0.5 text-slate-300 hover:bg-red-50 hover:text-red-400 transition-colors"
          title="Remove document"
        >
          ✕
        </button>
      )}

      {hovered && doc.summary && <DocumentDetail doc={doc} />}
    </div>
  )
}

export default DocumentItem
