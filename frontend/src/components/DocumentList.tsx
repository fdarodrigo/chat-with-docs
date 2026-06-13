import type { DocumentInfo } from '../types';

interface DocumentListProps {
  documents: DocumentInfo[];
  isLoading: boolean;
  onDelete: (docId: string) => Promise<void>;
}

/** Sidebar list of uploaded documents with chunk counts and delete buttons. */
export function DocumentList({ documents, isLoading, onDelete }: DocumentListProps) {
  if (isLoading && documents.length === 0) {
    return <p className="sidebar-loading">Loading documents…</p>;
  }

  if (documents.length === 0) {
    return <p className="sidebar-empty">No documents uploaded yet.</p>;
  }

  return (
    <ul className="sidebar-documents-list">
      {documents.map((doc) => (
        <li key={doc.doc_id} className="doc-card">
          <div className="doc-card-info">
            <p className="doc-card-name" title={doc.filename}>
              {doc.filename}
            </p>
            <p className="doc-card-meta">{doc.chunk_count} chunks</p>
          </div>
          <button
            type="button"
            onClick={() => void onDelete(doc.doc_id)}
            className="doc-delete-btn"
            aria-label={`Delete ${doc.filename}`}
          >
            Delete
          </button>
        </li>
      ))}
    </ul>
  );
}
