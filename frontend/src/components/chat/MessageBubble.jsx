// src/components/chat/MessageBubble.jsx
import { cn } from '@/lib/utils'
import CitationList from './CitationList'
import IntentBadge from './IntentBadge'

function MessageBubble({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[80%] rounded-2xl px-4 py-3 text-sm',
          isUser
            ? 'rounded-br-sm bg-slate-900 text-white'
            : 'rounded-bl-sm border border-slate-100 bg-white text-slate-700',
          message.isError && 'border-red-100 text-red-500'
        )}
      >
        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>

        {!isUser && (
          <>
            <CitationList citations={message.citations} />
            {message.intent && (
              <div className="mt-2">
                <IntentBadge intent={message.intent} />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default MessageBubble
