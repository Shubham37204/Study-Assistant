import { useState, useEffect } from 'react'

function OfflineBanner() {
  const [isOnline, setIsOnline] = useState(navigator.onLine)

  useEffect(() => {
    const handleOnline  = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online',  handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online',  handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  if (isOnline) return null

  return (
    <div className="flex h-8 shrink-0 items-center justify-center border-b border-amber-100 bg-amber-50 text-xs text-amber-700">
      No internet connection — uploads and queries won't work
    </div>
  )
}

export default OfflineBanner
