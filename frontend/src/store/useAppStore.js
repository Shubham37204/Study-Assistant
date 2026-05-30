import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useAppStore = create(
  persist(
    (set, get) => ({
      documents: [],
      selectedDocIds: [],

      addDocument: (doc) =>
        set((state) => {
          const exists = state.documents.some(
            (d) => d.document_id === doc.document_id
          )

          if (exists) return state

          return {
            documents: [doc, ...state.documents],
          }
        }),

      setDocuments: (docs) =>
        set({
          documents: docs,
        }),

      removeDocument: (docId) =>
        set((state) => ({
          documents: state.documents.filter(
            (d) => d.document_id !== docId
          ),
          selectedDocIds: state.selectedDocIds.filter(
            (id) => id !== docId
          ),
        })),

      clearDocuments: () =>
        set({
          documents: [],
          selectedDocIds: [],
        }),

      toggleDocSelection: (docId) =>
        set((state) => {
          const alreadySelected =
            state.selectedDocIds.includes(docId)

          return {
            selectedDocIds: alreadySelected
              ? state.selectedDocIds.filter(
                  (id) => id !== docId
                )
              : [...state.selectedDocIds, docId],
          }
        }),

      clearSelectedDocs: () =>
        set({
          selectedDocIds: [],
        }),

      messages: [],

      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),

      setMessages: (messages) =>
        set({
          messages,
        }),

      clearMessages: () =>
        set({
          messages: [],
        }),

      getSelectedDocuments: () => {
        const { documents, selectedDocIds } = get()

        return documents.filter((doc) =>
          selectedDocIds.includes(doc.document_id)
        )
      },
    }),
    {
      name: 'study-assistant',

      partialize: (state) => ({
        selectedDocIds: state.selectedDocIds,
      }),
    }
  )
)

export default useAppStore
