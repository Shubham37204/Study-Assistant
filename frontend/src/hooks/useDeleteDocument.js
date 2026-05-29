import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useAuth } from '@clerk/clerk-react'
import { deleteDocument } from '../api/documents'
import useAppStore from '../store/useAppStore'

export function useDeleteDocument() {
  const { userId } = useAuth()
  const removeDocument = useAppStore((state) => state.removeDocument)

  return useMutation({
    mutationFn: (documentId) => deleteDocument(documentId, userId),

    onSuccess: (_, documentId) => {
      removeDocument(documentId)
      toast.success('Document removed')
    },

    onError: () => {
      toast.error('Failed to remove document')
    },
  })
}
