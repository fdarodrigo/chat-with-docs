import { ChatInterface } from './components/ChatInterface';
import { DocumentList } from './components/DocumentList';
import { DocumentUploader } from './components/DocumentUploader';
import { useChat } from './hooks/useChat';
import { useDocuments } from './hooks/useDocuments';

function App() {
  const {
    documents,
    isLoading: documentsLoading,
    error: documentsError,
    uploadingFilename,
    uploadDocument,
    deleteDocument,
  } = useDocuments();
  const { messages, isLoading: chatLoading, error: chatError, sendMessage } = useChat();

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50 text-slate-900">
      <aside className="flex w-64 shrink-0 flex-col gap-4 overflow-y-auto border-r border-slate-200 bg-white p-4">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Chat With Your Docs</h1>
          <p className="mt-1 text-xs text-slate-500">Upload documents and ask questions about their content.</p>
        </div>

        <DocumentUploader onUpload={uploadDocument} uploadingFilename={uploadingFilename} />

        {documentsError && <p className="text-xs text-red-600">{documentsError}</p>}

        <div className="flex-1">
          <h2 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">Documents</h2>
          <DocumentList documents={documents} isLoading={documentsLoading} onDelete={deleteDocument} />
        </div>
      </aside>

      <main className="flex-1">
        <ChatInterface messages={messages} isLoading={chatLoading} error={chatError} onSend={sendMessage} />
      </main>
    </div>
  );
}

export default App;
