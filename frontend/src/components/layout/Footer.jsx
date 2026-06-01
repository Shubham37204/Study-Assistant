// src/components/layout/Footer.jsx
function Footer() {
  return (
    <footer className="shrink-0 border-t border-slate-100 bg-white px-6 py-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-slate-400">
          © {new Date().getFullYear()} Study Assistant
        </p>
        <p className="text-xs text-slate-300">
          FastAPI · LangGraph · Qdrant · React
        </p>
      </div>
    </footer>
  )
}

export default Footer
