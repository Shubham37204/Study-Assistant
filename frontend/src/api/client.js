import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
})

apiClient.interceptors.request.use(async (config) => {
  try {
    const token = await window.Clerk?.session?.getToken()

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  } catch {
    // Continue as anonymous/dev user if Clerk is not ready.
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    return Promise.reject(new Error(getApiErrorMessage(error)))
  }
)

function getApiErrorMessage(error) {
  const detail = error.response?.data?.detail

  if (typeof detail === 'string') {
    return detail
  }

  if (typeof detail?.detail === 'string') {
    return detail.detail
  }

  if (typeof detail?.error === 'string') {
    return detail.error
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item.msg)
      .filter(Boolean)
      .join(', ') || 'Validation failed'
  }

  return error.message || 'Request failed'
}

export default apiClient
