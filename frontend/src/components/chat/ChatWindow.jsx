import { useEffect, useRef } from 'react'
import useAppStore from '@/store/useAppStore'
import { useChatQuery } from '@/hooks/useQuery'
import MessageBubble from './MessageBubble'
import QueryInput from './QueryInput'

function ChatWindow() {
  const messages = useAppStore((state) => state.messages)
  const documents = useAppStore((state) => state.documents)
  const { mutate: ask, isPending } = useChatQuery()
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isPending])

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <EmptyState hasDocuments={documents.length > 0} onSuggest={ask} />
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
  )
}

function EmptyState({ hasDocuments, onSuggest }) {
  const suggestions = [
    'Summarize this document',
    'What are the key concepts?',
    'List the main topics',
  ]

  return (
    <div className="flex h-full flex-col items-center justify-center gap-4 text-center">
      {!hasDocuments ? (
        <>
          <p className="text-sm text-slate-500">
            Upload a document to get started
          </p>
          <p className="text-xs text-slate-400">
            Use the sidebar to upload PDFs, text files, or images
          </p>
        </>
      ) : (
        <>
          <p className="text-sm text-slate-500">
            Ask anything about your documents
          </p>
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
        </>
      )}
    </div>
  )
}

export default ChatWindow