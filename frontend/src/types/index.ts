/** Shared TypeScript types mirroring the backend's Pydantic models. */

export interface DocumentInfo {
  doc_id: string;
  filename: string;
  chunk_count: number;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
}

export interface DocumentUploadResponse {
  doc_id: string;
  filename: string;
  chunk_count: number;
  status: string;
}

export interface DocumentDeleteResponse {
  doc_id: string;
  status: string;
}

export type MessageRole = 'user' | 'assistant';

export interface ConversationMessage {
  role: MessageRole;
  content: string;
}

export interface SourceCitation {
  text: string;
  filename: string;
  page: number;
  score: number;
}

export interface ChatRequest {
  question: string;
  conversation_history: ConversationMessage[];
}

export interface ChatResponse {
  answer: string;
  sources: SourceCitation[];
  tokens_used: number;
}

/** A single message in the UI's chat transcript, including any assistant metadata. */
export interface ChatMessage extends ConversationMessage {
  id: string;
  sources?: SourceCitation[];
  tokens_used?: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  documents_count: number;
}
