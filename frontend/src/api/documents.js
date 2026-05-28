// src/api/documents.js
import apiClient from './client'

// Sends file as multipart form to POST /upload?user_id=...
// Returns the UploadResponse shape from FastAPI
export async function uploadDocument(file, userId) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiClient.post(
    `/upload?user_id=${encodeURIComponent(userId)}`,
    formData
  )

  return response.data
}