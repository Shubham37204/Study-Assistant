import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAppStore = create(
  persist(
    (set, get) => ({
      documents: [],
      selectedDocIds: [],

      addDocument: (doc) =>
        set((state) => {
          const exists = state.documents.some((d) => d.document_id === doc.document_id)
          if (exists) return state
          return { documents: [doc, ...state.documents] }
        }),

      setDocuments: (docs) => {
        const validIds = new Set(docs.map((d) => d.document_id))
        set((state) => ({
          documents: docs,
          selectedDocIds: state.selectedDocIds.filter((id) => validIds.has(id)),
        }))
      },

      removeDocument: (docId) =>
        set((state) => ({
          documents: state.documents.filter((d) => d.document_id !== docId),
          selectedDocIds: state.selectedDocIds.filter((id) => id !== docId),
        })),

      clearDocuments: () => set({ documents: [], selectedDocIds: [] }),

      toggleDocSelection: (docId) =>
        set((state) => {
          const already = state.selectedDocIds.includes(docId)
          return {
            selectedDocIds: already
              ? state.selectedDocIds.filter((id) => id !== docId)
              : [...state.selectedDocIds, docId],
          }
        }),

      clearSelectedDocs: () => set({ selectedDocIds: [] }),

      getSelectedDocuments: () => {
        const { documents, selectedDocIds } = get()
        return documents.filter((d) => selectedDocIds.includes(d.document_id))
      },

      conversations: {},

      _scopeKey: () => {
        const { selectedDocIds } = get()
        return [...selectedDocIds].sort().join(',') || '__global__'
      },

      addMessage: (message) => {
        const key = get()._scopeKey()
        set((state) => ({
          conversations: {
            ...state.conversations,
            [key]: [...(state.conversations[key] || []), message],
          },
        }))
      },

      clearCurrentMessages: () => {
        const key = get()._scopeKey()
        set((state) => ({
          conversations: {
            ...state.conversations,
            [key]: [],
          },
        }))
      },

      clearAllConversations: () => set({ conversations: {} }),
    }),
    {
      name: 'study-assistant',
      partialize: (state) => ({
        selectedDocIds: state.selectedDocIds,
        conversations: state.conversations, 
      }),
    }
  )
)

export default useAppStore
