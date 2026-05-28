// src/components/chat/QueryInput.jsx
import { useState } from 'react'
import { cn } from '@/lib/utils'
import useAppStore from '@/store/useAppStore'

function QueryInput({ onSubmit, isLoading }) {
  const [value, setValue] = useState('')
  const selectedDocIds = useAppStore((state) => state.selectedDocIds)

  function submit() {
    const text = value.trim()
    if (!text || isLoading) return
    onSubmit(text)
    setValue('')
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  // auto-resize textarea as user types
  function handleInput(e) {
    e.target.style.height = 'auto'
    e.target.style.height = `${e.target.scrollHeight}px`
  }

  return (
    <div className="shrink-0 border-t border-slate-100 bg-white p-4">
      {selectedDocIds.length > 0 && (
        <p className="mb-2 text-xs text-slate-400">
          Searching {selectedDocIds.length} selected doc
          {selectedDocIds.length > 1 ? 's' : ''}
        </p>
      )}

      <div className="flex items-end gap-2">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={isLoading}
          placeholder="Ask a question about your documents..."
          rows={1}
          className={cn(
            'flex-1 resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm',
            'max-h-36 focus:border-slate-400 focus:outline-none placeholder:text-slate-400',
            isLoading && 'cursor-not-allowed opacity-50'
          )}
        />
        <button
          onClick={submit}
          disabled={!value.trim() || isLoading}
          className="shrink-0 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          Send
        </button>
      </div>
    </div>
  )
}

export default QueryInput
