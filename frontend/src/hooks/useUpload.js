// src/hooks/useUpload.js — simplified, handles sync response correctly
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useAuth } from "@clerk/clerk-react";
import { uploadDocument } from "../api/documents";
import useAppStore from "../store/useAppStore";

const POLL_INTERVAL = 2000;
const MAX_POLLS = 90; // 3 minutes

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

      // ── sync path (eager mode / dev) ──────────────────────────────────
      // result already available — no polling needed
      if (!response.async && response.status === "success" && response.result) {
        toast.dismiss(toastId);
        return { ...response.result, _toastId: toastId };
      }

      // ── async path (production with Redis + Celery) ───────────────────
      if (response.job_id) {
        try {
          const result = await pollJobStatus(response.job_id, toastId);
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
      console.log("UPLOAD SUCCESS", data);
      toast.dismiss(data._toastId);
      toast.success(`"${data.file_name}" ready — ${data.total_chunks} chunks`, {
        duration: 4000,
      });
      console.log("UPLOAD SUCCESS", data);
      addDocument(data);
      console.log("STORE AFTER ADD", useAppStore.getState().documents);
    },

    onError: (error) => {
      toast.error(error.message || "Upload failed");
    },
  });
}

async function pollJobStatus(jobId, toastId, attempts = 0) {
  if (attempts > MAX_POLLS) {
    throw new Error("Upload timed out — backend may be slow");
  }

  const res = await fetch(`/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Job poll failed: ${res.status}`);

  const data = await res.json();

  if (data.status === "success") return data.result;
  if (data.status === "failed")
    throw new Error(data.error || "Ingestion failed");

  await new Promise((r) => setTimeout(r, POLL_INTERVAL));
  return pollJobStatus(jobId, toastId, attempts + 1);
}
