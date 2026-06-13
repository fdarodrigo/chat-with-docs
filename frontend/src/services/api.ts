/** Typed wrapper around the backend REST API. */

import type {
  ChatRequest,
  ChatResponse,
  DocumentDeleteResponse,
  DocumentListResponse,
  DocumentUploadResponse,
  HealthResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

/** Error thrown when the backend returns a non-2xx response. */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, options);

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // Response body was not JSON; fall back to the status text.
    }
    throw new ApiError(response.status, detail);
  }

  return (await response.json()) as T;
}

export const api = {
  /** Fetch service health and document count. */
  async getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/api/health');
  },

  /** List all documents currently stored in the vector store. */
  async listDocuments(): Promise<DocumentListResponse> {
    return request<DocumentListResponse>('/api/documents');
  },

  /** Upload a document (PDF, DOCX, or TXT) for ingestion. */
  async uploadDocument(file: File): Promise<DocumentUploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    return request<DocumentUploadResponse>('/api/documents/upload', {
      method: 'POST',
      body: formData,
    });
  },

  /** Delete a document and all of its chunks. */
  async deleteDocument(docId: string): Promise<DocumentDeleteResponse> {
    return request<DocumentDeleteResponse>(`/api/documents/${docId}`, {
      method: 'DELETE',
    });
  },

  /** Ask a question and get a grounded answer with source citations. */
  async sendChatMessage(payload: ChatRequest): Promise<ChatResponse> {
    return request<ChatResponse>('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },
};
