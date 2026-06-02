import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useAuth } from "@clerk/clerk-react";
import { uploadDocument } from "../api/documents";
import useAppStore from "../store/useAppStore";
import apiClient from '../api/client'

const POLL_INTERVAL = 2000;
const MAX_POLLS = 90; 
export function useUpload() {
  const { userId } = useAuth();
  const addDocument = useAppStore((state) => state.addDocument);

  return useMutation({
    mutationFn: async (file) => {
      const toastId = `upload-${Date.now()}`;

      toast.loading(`Processing "${file.name}"...`, { id: toastId });

      let response;
      try {
        response = await uploadDocument(file, userId);
      } catch (err) {
        toast.dismiss(toastId);
        throw err;
      }
      if (!response.async && response.status === "success" && response.result) {
        toast.dismiss(toastId);
        return { ...response.result, _toastId: toastId };
      }

      if (response.job_id) {
        try {
          const result = await pollJobStatus(response.job_id);
          return { ...result, _toastId: toastId };
        } catch (err) {
          toast.dismiss(toastId);
          throw err;
        }
      }

      toast.dismiss(toastId);
      throw new Error(response.error || "Upload returned unexpected response");
    },

    onSuccess: (data) => {
      toast.dismiss(data._toastId);
      toast.success(`"${data.file_name}" ready — ${data.total_chunks} chunks`, {
        duration: 4000,
      });
      addDocument(data);
    },

    onError: (error) => {
      toast.error(error.message || "Upload failed");
    },
  });
}

async function pollJobStatus(jobId, attempts = 0) {  
  if (attempts > MAX_POLLS) {
    throw new Error('Upload timed out — backend may be slow')
  }
  const res  = await apiClient.get(`/jobs/${jobId}`)
  const data = res.data

  if (data.status === 'success') return data.result
  if (data.status === 'failed')  throw new Error(data.error || 'Ingestion failed')

  await new Promise((r) => setTimeout(r, POLL_INTERVAL))
  return pollJobStatus(jobId, attempts + 1)  
}