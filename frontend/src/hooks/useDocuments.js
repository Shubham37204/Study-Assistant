import { useEffect } from "react";
import { useAuth } from "@clerk/clerk-react";
import { fetchDocuments } from "../api/documents";
import useAppStore from "../store/useAppStore";

export function useDocuments() {
  const { userId, isLoaded } = useAuth();
  const setDocuments = useAppStore((state) => state.setDocuments);

  useEffect(() => {
    if (!isLoaded || !userId) return;

    fetchDocuments(userId)
      .then((docs) => {
        setDocuments(docs); 
      })
      .catch((err) => {
        console.warn("Failed to fetch documents:", err.message);
      });
  }, [userId, isLoaded, setDocuments]);
}
