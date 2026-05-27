// src/hooks/useAuth.js
import { useUser, useAuth as useClerkAuth } from '@clerk/clerk-react'

// Thin wrapper around Clerk so the rest of the app
// doesn't depend directly on Clerk's API shape.
// If we ever swap auth providers, only this file changes.
export function useAuth() {
  const { user, isLoaded: userLoaded } = useUser()
  const { isSignedIn, isLoaded: authLoaded, userId } = useClerkAuth()

  return {
    user,
    userId,
    isSignedIn: !!isSignedIn,
    isLoaded: userLoaded && authLoaded,
  }
}