import { useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { fetchDocuments } from '../api/documents'
import useAppStore from '../store/useAppStore'

const MAX_ATTEMPTS = 5
const BASE_DELAY_MS = 2000

export function useDocuments() {
  const { userId, isLoaded } = useAuth()
  const setDocuments = useAppStore((state) => state.setDocuments)

  useEffect(() => {
    if (!isLoaded || !userId) return

    let cancelled = false
    let attempt = 0

    async function tryFetch() {
      while (attempt < MAX_ATTEMPTS && !cancelled) {
        try {
          const docs = await fetchDocuments(userId)
          if (!cancelled) setDocuments(docs)
          return
        } catch {
          attempt++
          if (attempt < MAX_ATTEMPTS && !cancelled) {
            await new Promise((r) => setTimeout(r, BASE_DELAY_MS * attempt))
          }
        }
      }
    }

    tryFetch()

    return () => { cancelled = true }
  }, [userId, isLoaded, setDocuments])
}