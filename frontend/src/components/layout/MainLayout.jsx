import Header from './Header'
import Sidebar from './Sidebar'
import Footer from './Footer'
import ErrorBoundary from '../ui/ErrorBoundary'
import OfflineBanner from '../ui/OfflineBanner'

function MainLayout({ children }) {
  return (
    <div className="flex h-screen flex-col overflow-hidden bg-white">
      <OfflineBanner />
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <div className="hidden md:flex md:shrink-0">
          <ErrorBoundary>
            <Sidebar />
          </ErrorBoundary>
        </div>

        <main className="flex flex-1 flex-col overflow-hidden">
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </main>
      </div>

      <Footer />
    </div>
  )
}

export default MainLayout