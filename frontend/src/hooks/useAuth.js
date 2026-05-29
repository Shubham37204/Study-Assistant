import { useUser, useAuth as useClerkAuth } from '@clerk/clerk-react'

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
