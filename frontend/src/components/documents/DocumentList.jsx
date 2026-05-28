// src/components/documents/DocumentList.jsx
import useAppStore from '@/store/useAppStore'
import DocumentItem from './DocumentItem'

function DocumentList() {
  const documents = useAppStore((state) => state.documents)

  if (documents.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-1 py-10">
        <p className="text-xs text-slate-400">No documents yet</p>
        <p className="text-xs text-slate-300">Upload one above</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <DocumentItem key={doc.document_id} doc={doc} />
      ))}
    </div>
  )
}

export default DocumentList
