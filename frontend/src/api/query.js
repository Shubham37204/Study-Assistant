// src/api/query.js
import apiClient from './client'

export async function sendQuery({ queryText, userId, documentIds }) {
  const response = await apiClient.post('/query', {
    query_text: queryText,
    user_id: userId,
    document_ids: documentIds,
    search_type: 'hybrid',
  })
  return response.data
}
