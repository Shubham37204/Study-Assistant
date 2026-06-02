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
  const isFailed = doc.status === 'failed' || doc.total_chunks === 0
  const isSelected = !isFailed && selectedDocIds.includes(doc.document_id)

  function handleDelete(e) {
    e.stopPropagation()
    remove(doc.document_id)
  }

  function handleToggle() {
    if (!isFailed) toggleDocSelection(doc.document_id)
  }

  return (
    <div
      role="button"
      aria-disabled={isFailed}
      onClick={handleToggle}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      className={cn(
        'relative flex items-start gap-2.5 rounded-lg border p-3 transition-colors',
        isFailed
          ? 'cursor-not-allowed border-red-100 bg-red-50 opacity-75'
          : 'cursor-pointer',
        isSelected
          ? 'border-slate-300 bg-white'
          : !isFailed && 'border-slate-100 bg-white hover:border-slate-200',
        deleting && 'opacity-40 pointer-events-none'
      )}
    >
      <input
        type="checkbox"
        checked={isSelected}
        disabled={isFailed}
        onChange={handleToggle}
        onClick={(e) => e.stopPropagation()}
        className={cn(
          'mt-0.5 h-3.5 w-3.5 shrink-0 accent-slate-800',
          isFailed ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
        )}
      />

      <div className="min-w-0 flex-1">
        <p title={doc.file_name} className="truncate text-xs font-medium text-slate-700">
          {doc.file_name}
        </p>
        {isFailed ? (
          <p className="mt-1.5 text-xs text-red-500">
            Failed - no usable text extracted
          </p>
        ) : (
          <div className="mt-1.5 flex items-center gap-2">
            <span className={cn('rounded px-1.5 py-0.5 text-xs font-medium', typeColors[doc.file_type] ?? 'bg-slate-100 text-slate-500')}>
              {doc.file_type}
            </span>
            <span className="text-xs text-slate-400">{doc.total_chunks} chunks</span>
          </div>
        )}
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

      {hovered && !isFailed && doc.summary && <DocumentDetail doc={doc} />}
    </div>
  )
}

export default DocumentItem
