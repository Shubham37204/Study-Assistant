import UploadZone from '../documents/UploadZone'
import DocumentList from '../documents/DocumentList'

function Sidebar() {
  return (
    <aside className="flex w-72 shrink-0 flex-col border-r border-slate-100 bg-slate-50">
      <div className="shrink-0 border-b border-slate-100 p-4">
        <UploadZone />
      </div>

      <div className="flex flex-1 flex-col overflow-y-auto p-4">
        <p className="mb-3 text-xs font-medium uppercase tracking-wider text-slate-400">
          Documents
        </p>
        <DocumentList />
      </div>
    </aside>
  )
}

export default Sidebar