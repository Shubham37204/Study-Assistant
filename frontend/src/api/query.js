import apiClient from './client'

export async function sendQuery({
  queryText,
  userId,
  documentIds,
  conversationHistory = [],
}) {
  const response = await apiClient.post('/query', {
    query_text: queryText,
    user_id: userId,
    document_ids: documentIds,
    search_type: 'hybrid',
    conversation_history: conversationHistory.slice(-6).map((m) => ({
      role: m.role,
      content: m.content,
    })),
  })
  return response.data
}
