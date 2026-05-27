// src/App.jsx
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@clerk/clerk-react'
import AuthPage from './pages/AuthPage'
import DashboardPage from './pages/DashboardPage'

// Keeps the route protection logic in one place.
// Any route wrapped in this redirects to / if the user isn't signed in.
function ProtectedRoute({ children }) {
  const { isSignedIn, isLoaded } = useAuth()

  if (!isLoaded) return null

  if (!isSignedIn) {
    return <Navigate to="/" replace />
  }

  return children
}

function App() {
  return (
    <Routes>
      {/* public — the sign-in page */}
      <Route path="/" element={<AuthPage />} />

      {/* protected — requires auth */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
