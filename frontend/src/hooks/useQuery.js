// src/hooks/useQuery.js
// Named useChatQuery to avoid collision with TanStack's useQuery
import { useMutation } from '@tanstack/react-query'
import { useAuth } from '@clerk/clerk-react'
import { sendQuery } from '../api/query'
import useAppStore from '../store/useAppStore'

export function useChatQuery() {
  const { userId } = useAuth()
  const { addMessage, selectedDocIds } = useAppStore()

  return useMutation({
    mutationFn: (queryText) =>
      sendQuery({ queryText, userId, documentIds: selectedDocIds }),

    onMutate: (queryText) => {
      // add user message immediately — no waiting
      addMessage({
        id: crypto.randomUUID(),
        role: 'user',
        content: queryText,
        citations: [],
        intent: null,
        timestamp: Date.now(),
      })
    },

    onSuccess: (data) => {
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.answer,
        citations: data.citations ?? [],
        intent: data.intent,
        timestamp: Date.now(),
      })
    },

    onError: () => {
      addMessage({
        id: crypto.randomUUID(),
        role: 'assistant',
        content: 'Something went wrong. Check that the backend is running.',
        citations: [],
        intent: null,
        isError: true,
        timestamp: Date.now(),
      })
    },
  })
}
