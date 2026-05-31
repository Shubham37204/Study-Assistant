import axios from 'axios'

const baseURL = import.meta.env.DEV
  ? ''
  : (import.meta.env.VITE_API_BASE_URL || '')

const apiClient = axios.create({
  baseURL,
  timeout: 180000, 
})

apiClient.interceptors.request.use(async (config) => {
  try {
    const token = await window.Clerk?.session?.getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
  } catch {
    // Clerk not ready
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail?.detail ||
      error.response?.data?.detail ||
      error.message ||
      'Request failed'
    return Promise.reject(new Error(message))
  }
)

export default apiClient
