import { useEffect, useRef } from "react";
import useAppStore from "@/store/useAppStore";
import { useChatQuery } from "@/hooks/useQuery";
import MessageBubble from "./MessageBubble";
import QueryInput from "./QueryInput";

const EMPTY_MESSAGES = []

function ChatWindow() {
  const selectedIds    = useAppStore((s) => s.selectedDocIds)
  const documents      = useAppStore((s) => s.documents)
  const clearCurrent   = useAppStore((s) => s.clearCurrentMessages)
  const { mutate: ask, isPending } = useChatQuery()
  const bottomRef = useRef(null)

  // Select messages based on scope key - use constant empty array to avoid new references
  const messages = useAppStore((s) => {
    const key = [...s.selectedDocIds].sort().join(',') || '__global__'
    return s.conversations[key] || EMPTY_MESSAGES
  })

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex h-full flex-col">

      {messages.length > 0 && (
        <div className="flex shrink-0 items-center justify-between border-b border-slate-100 px-6 py-2">
          <span className="text-xs text-slate-400">
            {selectedIds.length > 0
              ? `${messages.length} messages — ${selectedIds.length} doc${selectedIds.length > 1 ? 's' : ''}`
              : `${messages.length} messages — no doc selected`}
          </span>
          <button
            onClick={clearCurrent}
            className="text-xs text-slate-400 hover:text-slate-600 transition-colors"
          >
            Clear chat
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <EmptyState documents={documents} selectedIds={selectedIds} onSuggest={ask} />
        ) : (
          <div className="space-y-4 pb-2">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isPending && <TypingIndicator />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      <QueryInput onSubmit={ask} isLoading={isPending} />
    </div>
  )
}

function EmptyState({ documents, selectedIds, onSuggest }) {
  const selectedDocs = documents.filter((d) =>
    selectedIds.includes(d.document_id),
  );
  const suggestions = [
    "Summarize this document",
    "What are the key concepts?",
    "List the main topics",
  ];

  if (documents.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-center">
        <p className="text-sm text-slate-500">
          Upload a document to get started
        </p>
        <p className="text-xs text-slate-400">
          Use the sidebar to upload PDFs, text files, or images
        </p>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col items-start justify-center gap-6 max-w-2xl mx-auto w-full">
      {selectedDocs.length > 0 && (
        <div className="w-full space-y-3">
          {selectedDocs.map((doc) => (
            <div
              key={doc.document_id}
              className="rounded-xl border border-slate-100 bg-slate-50 p-4"
            >
              <div className="mb-2 flex items-center gap-2">
                <span className="rounded bg-red-50 px-1.5 py-0.5 text-xs font-medium text-red-600">
                  {doc.file_type}
                </span>
                <span className="text-sm font-medium text-slate-700 truncate">
                  {doc.file_name}
                </span>
                <span className="ml-auto text-xs text-slate-400 shrink-0">
                  {doc.total_chunks} chunks
                </span>
              </div>
              {doc.summary && (
                <p className="text-xs leading-relaxed text-slate-500 line-clamp-3">
                  {doc.summary}
                </p>
              )}
              {doc.key_topics?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {doc.key_topics.slice(0, 5).map((t) => (
                    <span
                      key={t}
                      className="rounded-full bg-white border border-slate-200 px-2 py-0.5 text-xs text-slate-500"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* prompt + suggestions */}
      <div className="w-full text-center">
        <p className="mb-3 text-sm text-slate-500">
          {selectedDocs.length > 0
            ? "Document ready — ask anything below"
            : "Check a document in the sidebar, then ask a question"}
        </p>
        {selectedDocs.length > 0 && (
          <div className="flex flex-wrap justify-center gap-2">
            {suggestions.map((s) => (
              <button
                key={s}
                onClick={() => onSuggest(s)}
                className="rounded-full border border-slate-200 px-3 py-1.5 text-xs text-slate-500 transition-colors hover:border-slate-300 hover:bg-slate-50"
              >
                {s}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="rounded-2xl rounded-bl-sm border border-slate-100 bg-white px-4 py-3">
        <div className="flex items-center gap-1">
          {[0, 150, 300].map((delay) => (
            <span
              key={delay}
              className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-300"
              style={{ animationDelay: `${delay}ms` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default ChatWindow;
