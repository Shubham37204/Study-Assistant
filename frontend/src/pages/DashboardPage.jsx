// src/pages/DashboardPage.jsx
import { UserButton, useUser } from '@clerk/clerk-react'

// UserButton renders the user's avatar (or initials).
// Clicking it opens a Clerk-managed dropdown:
//   — Manage account (update photo, name, email)
//   — Sign out
// afterSignOutUrl sends the user back to landing after signing out.

function DashboardPage() {
  const { user } = useUser()

  return (
    <div className="min-h-screen bg-white">

      {/* temporary header — Phase 4 replaces this with MainLayout */}
      <header className="flex items-center justify-between border-b border-slate-100 px-6 py-3">
        <span className="text-sm font-semibold text-slate-800">
          Study Assistant
        </span>

        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500">
            {user?.firstName ?? 'User'}
          </span>
          <UserButton afterSignOutUrl="/" />
        </div>
      </header>

      <main className="flex h-[calc(100vh-57px)] items-center justify-center">
        <p className="text-sm text-slate-400">Dashboard layout — Phase 4</p>
      </main>

    </div>
  )
}

export default DashboardPage