import type { DocumentInfo } from '../types';

interface DocumentListProps {
  documents: DocumentInfo[];
  isLoading: boolean;
  onDelete: (docId: string) => Promise<void>;
}

/** Sidebar list of uploaded documents with chunk counts and delete buttons. */
export function DocumentList({ documents, isLoading, onDelete }: DocumentListProps) {
  if (isLoading && documents.length === 0) {
    return <p className="text-sm text-slate-500">Loading documents…</p>;
  }

  if (documents.length === 0) {
    return <p className="text-sm text-slate-500">No documents uploaded yet.</p>;
  }

  return (
    <ul className="space-y-2">
      {documents.map((doc) => (
        <li
          key={doc.doc_id}
          className="flex items-start justify-between gap-2 rounded-md border border-slate-200 bg-white p-2 text-sm"
        >
          <div className="min-w-0">
            <p className="truncate font-medium text-slate-800" title={doc.filename}>
              {doc.filename}
            </p>
            <p className="text-xs text-slate-500">{doc.chunk_count} chunks</p>
          </div>
          <button
            type="button"
            onClick={() => void onDelete(doc.doc_id)}
            className="shrink-0 rounded px-2 py-1 text-xs font-medium text-slate-400 transition-colors hover:bg-red-50 hover:text-red-600"
            aria-label={`Delete ${doc.filename}`}
          >
            Delete
          </button>
        </li>
      ))}
    </ul>
  );
}
