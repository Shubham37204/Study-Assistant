import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { useAuth } from '@clerk/clerk-react'
import { uploadDocument } from '../api/documents'
import useAppStore from '../store/useAppStore'

export function useUpload() {
  const { userId } = useAuth()
  const addDocument = useAppStore((state) => state.addDocument)

  return useMutation({
    mutationFn: (file) => {
      if (!userId) throw new Error('Not signed in')
      return uploadDocument(file, userId)
    },

    onMutate: () => {
      toast.loading('Processing document...', { id: 'upload' })
    },

    onSuccess: (data) => {
      toast.success(
        `"${data.file_name}" indexed — ${data.total_chunks} chunks`,
        { id: 'upload', duration: 4000 }
      )
      addDocument(data)
    },

    onError: (error) => {
      toast.error(error.message || 'Upload failed', { id: 'upload' })
    },
  })
}
