import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import Spinner from './components/ui/Spinner'

const AuthPage      = lazy(() => import('./pages/AuthPage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))

function ProtectedRoute({ children }) {
  const { isSignedIn, isLoaded } = useAuth()
  if (!isLoaded) return null
  if (!isSignedIn) return <Navigate to="/" replace />
  return children
}

function PageLoader() {
  return (
    <div className="flex h-screen items-center justify-center">
      <Spinner className="h-5 w-5" />
    </div>
  )
}

function App() {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<AuthPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </Suspense>
  )
}

export default App
