// src/tests/SystemTest.jsx
// Temporary test component — add to App.jsx at route /test
// Remove before production deploy

import { useState } from 'react'
import { useAuth } from '@clerk/clerk-react'
import apiClient from '../api/client'

const TEST_CONTENT = 'FastAPI is a modern Python web framework for building APIs. It supports async, type hints, and automatic OpenAPI documentation.'

function makeTestFile() {
  const blob = new Blob([TEST_CONTENT], { type: 'text/plain' })
  return new File([blob], 'frontend_test.txt', { type: 'text/plain' })
}

const TESTS = [
  {
    name: '1. Backend Health',
    run: async () => {
      const r = await apiClient.get('/health')
      if (r.data.status !== 'ok') throw new Error('Status not ok')
      return r.data
    },
  },
  {
    name: '2. Upload Text File',
    run: async (userId) => {
      const formData = new FormData()
      formData.append('file', makeTestFile())
      const r = await apiClient.post(
        `/upload?user_id=${encodeURIComponent(userId)}`,
        formData
      )
      const d = r.data
      // sync path: result is nested
      const result = d.result ?? d
      if (!result.document_id) throw new Error('No document_id in response')
      if (!result.file_type)   throw new Error('file_type missing — check IngestionResult')
      if (typeof result.summary !== 'string') throw new Error(`summary is ${typeof result.summary}, expected string`)
      return {
        document_id: result.document_id,
        file_name:   result.file_name,
        file_type:   result.file_type,
        total_chunks: result.total_chunks,
        summary_preview: result.summary?.slice(0, 80),
        key_topics:  result.key_topics,
      }
    },
  },
  {
    name: '3. Fetch Document List',
    run: async (userId) => {
      const r = await apiClient.get(`/documents?user_id=${encodeURIComponent(userId)}`)
      if (!Array.isArray(r.data)) throw new Error('Expected array')
      return { count: r.data.length, first: r.data[0]?.file_name ?? 'none' }
    },
  },
  {
    name: '4. Send Query (no doc filter)',
    run: async (userId) => {
      const r = await apiClient.post('/query', {
        query_text: 'What is FastAPI used for?',
        user_id: userId,
        document_ids: [],
        search_type: 'hybrid',
        conversation_history: [],
      })
      const d = r.data
      if (!d.answer) throw new Error('No answer in response')
      return {
        answer_preview: d.answer.slice(0, 100),
        intent: d.intent,
        citations: d.citations?.length ?? 0,
      }
    },
  },
  {
    name: '5. Send Query (follow-up context)',
    run: async (userId) => {
      const r = await apiClient.post('/query', {
        query_text: 'Can you expand on that?',
        user_id: userId,
        document_ids: [],
        search_type: 'hybrid',
        conversation_history: [
          { role: 'user',      content: 'What is FastAPI?' },
          { role: 'assistant', content: 'FastAPI is a Python web framework.' },
        ],
      })
      if (!r.data.answer) throw new Error('No answer')
      return { answer_preview: r.data.answer.slice(0, 100) }
    },
  },
]

export default function SystemTest() {
  const { userId, isLoaded } = useAuth()
  const [results, setResults]   = useState([])
  const [running, setRunning]   = useState(false)
  const [summary, setSummary]   = useState(null)

  async function runAll() {
    if (!isLoaded || !userId) return
    setRunning(true)
    setResults([])
    setSummary(null)
    let passed = 0

    for (const test of TESTS) {
      const start = Date.now()
      try {
        const result = await test.run(userId)
        const ms = Date.now() - start
        setResults((prev) => [...prev, { name: test.name, status: 'pass', result, ms }])
        passed++
      } catch (err) {
        const ms = Date.now() - start
        setResults((prev) => [...prev, { name: test.name, status: 'fail', error: err.message, ms }])
      }
    }

    setSummary({ passed, total: TESTS.length })
    setRunning(false)
  }

  if (!isLoaded) return <div className="p-6 text-sm text-slate-400">Loading auth...</div>
  if (!userId)   return <div className="p-6 text-sm text-slate-400">Sign in to run tests</div>

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="mx-auto max-w-2xl">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-800">Frontend System Test</h1>
            <p className="text-xs text-slate-400">user_id: {userId.slice(0, 24)}...</p>
          </div>
          <button
            onClick={runAll}
            disabled={running}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-40"
          >
            {running ? 'Running...' : 'Run All Tests'}
          </button>
        </div>

        {summary && (
          <div className={`mb-4 rounded-lg p-3 text-sm font-medium ${
            summary.passed === summary.total
              ? 'bg-green-50 text-green-700'
              : 'bg-red-50 text-red-700'
          }`}>
            {summary.passed}/{summary.total} passed
            {summary.passed === summary.total
              ? ' — all systems operational'
              : ' — fix failures before demo'}
          </div>
        )}

        <div className="space-y-3">
          {results.map((r, i) => (
            <div
              key={i}
              className={`rounded-xl border p-4 ${
                r.status === 'pass'
                  ? 'border-green-100 bg-white'
                  : 'border-red-100 bg-white'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-700">
                  {r.status === 'pass' ? '✓' : '✗'} {r.name}
                </span>
                <span className="text-xs text-slate-400">{r.ms}ms</span>
              </div>

              {r.status === 'pass' ? (
                <pre className="mt-2 overflow-x-auto rounded bg-slate-50 p-2 text-xs text-slate-600">
                  {JSON.stringify(r.result, null, 2)}
                </pre>
              ) : (
                <p className="mt-1 text-xs text-red-600">{r.error}</p>
              )}
            </div>
          ))}
        </div>

        {results.length === 0 && !running && (
          <div className="rounded-xl border border-slate-100 p-8 text-center text-sm text-slate-400">
            Click "Run All Tests" to start diagnostics
          </div>
        )}
      </div>
    </div>
  )
}
