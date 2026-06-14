import { useCallback, useEffect, useState } from 'react';
import { ApiError, api } from '../services/api';
import type { DocumentInfo } from '../types';

interface UseDocumentsResult {
  documents: DocumentInfo[];
  isLoading: boolean;
  isInitialLoadComplete: boolean;
  error: string | null;
  uploadingFilename: string | null;
  refresh: () => Promise<void>;
  uploadDocument: (file: File) => Promise<void>;
  deleteDocument: (docId: string) => Promise<void>;
}

/** Manages the list of uploaded documents: fetching, uploading, and deleting. */
export function useDocuments(): UseDocumentsResult {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isInitialLoadComplete, setIsInitialLoadComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadingFilename, setUploadingFilename] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.listDocuments();
      setDocuments(response.documents);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to load documents.');
    } finally {
      setIsLoading(false);
      setIsInitialLoadComplete(true);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const uploadDocument = useCallback(
    async (file: File) => {
      setError(null);
      setUploadingFilename(file.name);
      try {
        await api.uploadDocument(file);
        await refresh();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Failed to upload document.');
      } finally {
        setUploadingFilename(null);
      }
    },
    [refresh],
  );

  const deleteDocument = useCallback(
    async (docId: string) => {
      setError(null);
      try {
        await api.deleteDocument(docId);
        await refresh();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Failed to delete document.');
      }
    },
    [refresh],
  );

  return { documents, isLoading, isInitialLoadComplete, error, uploadingFilename, refresh, uploadDocument, deleteDocument };
}
