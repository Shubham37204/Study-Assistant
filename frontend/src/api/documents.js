import apiClient from './client'

export async function uploadDocument(file, userId) {
  const formData = new FormData()
  formData.append('file', file)
  const response = await apiClient.post(
    `/upload?user_id=${encodeURIComponent(userId)}`,
    formData
  )
  return response.data
}

export async function deleteDocument(documentId, userId) {
  await apiClient.delete(
    `/documents/${documentId}?user_id=${encodeURIComponent(userId)}`
  )
}
