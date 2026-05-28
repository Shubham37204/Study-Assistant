// src/components/ui/ErrorBoundary.jsx
// Class component — error boundaries can't be hooks in React 18.
// Wraps sidebar and chat area independently so one crashing doesn't kill the other.
import { Component } from 'react'

class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('[ErrorBoundary]', error, info.componentStack)
  }

  reset() {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-full flex-col items-center justify-center gap-3 p-6">
          <p className="text-sm font-medium text-slate-700">Something went wrong</p>
          <p className="max-w-xs text-center text-xs text-slate-400">
            {this.state.error?.message ?? 'An unexpected error occurred'}
          </p>
          <button
            onClick={() => this.reset()}
            className="rounded-md bg-slate-100 px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-200"
          >
            Try again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary