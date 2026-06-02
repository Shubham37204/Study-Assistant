import { useMutation } from '@tanstack/react-query'
import { useAuth } from '@clerk/clerk-react'
import { sendQuery } from '../api/query'
import useAppStore from '../store/useAppStore'

const EMPTY_MESSAGES = []

export function useChatQuery() {
  const { userId } = useAuth()
  const { addMessage, selectedDocIds } = useAppStore()

  return useMutation({
    mutationFn: (queryText) => {
      const state = useAppStore.getState()
      const key = [...state.selectedDocIds].sort().join(',') || '__global__'
      const messages = state.conversations[key] || EMPTY_MESSAGES
      const history = messages.slice(-6)
      return sendQuery({
        queryText,
        userId,
        documentIds: selectedDocIds,
        conversationHistory: history,
      })
    },

    onMutate: (queryText) => {
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