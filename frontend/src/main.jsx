// src/main.jsx

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ClerkProvider } from '@clerk/clerk-react'
import { QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'

import App from './App.jsx'
import { queryClient } from '@/lib/queryClient'

import './index.css'

const clerkKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!clerkKey) {
  throw new Error(
    'VITE_CLERK_PUBLISHABLE_KEY is missing in .env'
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ClerkProvider publishableKey={clerkKey}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />

          <Toaster
            position="top-right"
            richColors
            closeButton
          />
        </BrowserRouter>
      </QueryClientProvider>
    </ClerkProvider>
  </StrictMode>
)
