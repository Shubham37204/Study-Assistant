import { UserButton, useUser } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'

function Header() {
  const { user } = useUser()

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-slate-100 px-6">
      <Link to="/" className="text-sm font-semibold text-slate-800">
        Study Assistant
      </Link>

      <div className="flex items-center gap-3">
        <span className="text-sm text-slate-400">
          {user?.firstName ?? ''}
        </span>
        <UserButton afterSignOutUrl="/" />
      </div>
    </header>
  )
}

export default Header