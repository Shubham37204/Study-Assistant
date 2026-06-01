import { SignInButton, SignedIn, SignedOut } from '@clerk/clerk-react'
import { Link } from 'react-router-dom'
import Footer from '../components/layout/Footer'

const features = [
  {
    title: 'Upload anything',
    desc: 'PDFs, text files, images, or links. Extracted and indexed automatically.',
  },
  {
    title: 'Hybrid search',
    desc: 'Vector + BM25 retrieval with reranking. Finds the right context every time.',
  },
  {
    title: 'Cited answers',
    desc: 'Every answer references the exact source chunk from your documents.',
  },
]

function AuthPage() {
  return (
    <div className="flex min-h-screen flex-col bg-white">

      {/* nav */}
      <header className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
        <span className="text-sm font-semibold text-slate-800">Study Assistant</span>
        <div>
          <SignedOut>
            <SignInButton mode="modal">
              <button className="text-sm text-slate-500 hover:text-slate-900 transition-colors">
                Sign in
              </button>
            </SignInButton>
          </SignedOut>
          <SignedIn>
            <Link to="/dashboard" className="text-sm text-slate-500 hover:text-slate-900 transition-colors">
              Dashboard →
            </Link>
          </SignedIn>
        </div>
      </header>

      {/* hero */}
      <main className="flex flex-1 flex-col items-center justify-center px-6 py-28 text-center">
        <span className="mb-5 inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-500">
          RAG · Semantic Search · Grounded Answers
        </span>
        <h1 className="mb-4 max-w-lg text-4xl font-semibold tracking-tight text-slate-900">
          Ask questions about your own notes
        </h1>
        <p className="mb-9 max-w-md text-base leading-relaxed text-slate-500">
          Upload PDFs, text files, or links. Get answers grounded in your
          material — with citations back to the source.
        </p>

        <SignedOut>
          <SignInButton mode="modal">
            <button className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-700 transition-colors">
              Get started
            </button>
          </SignInButton>
        </SignedOut>

        <SignedIn>
          <Link
            to="/dashboard"
            className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-700 transition-colors"
          >
            Open dashboard →
          </Link>
        </SignedIn>
      </main>

      {/* features */}
      <section className="mx-auto grid max-w-2xl grid-cols-1 gap-3 px-6 pb-16 sm:grid-cols-3">
        {features.map((f) => (
          <div key={f.title} className="rounded-xl border border-slate-100 p-5">
            <p className="mb-1.5 text-sm font-medium text-slate-800">{f.title}</p>
            <p className="text-sm leading-relaxed text-slate-500">{f.desc}</p>
          </div>
        ))}
      </section>

      <Footer />
    </div>
  )
}

export default AuthPage
