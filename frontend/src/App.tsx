import { useState } from 'react';
import { AnimatedInput } from './components/AnimatedInput';
import { ChatInterface } from './components/ChatInterface';
import { DocumentList } from './components/DocumentList';
import { DocumentUploader } from './components/DocumentUploader';
import { useChat } from './hooks/useChat';
import { useDocuments } from './hooks/useDocuments';

function App() {
  const {
    documents,
    isLoading: documentsLoading,
    isInitialLoadComplete,
    error: documentsError,
    uploadingFilename,
    uploadDocument,
    deleteDocument,
  } = useDocuments();
  const { messages, isLoading: chatLoading, error: chatError, sendMessage } = useChat();
  const [landingInput, setLandingInput] = useState('');
  const hasContent = messages.length > 0 || documents.length > 0;

  const handleLandingSubmit = () => {
    const question = landingInput.trim();
    if (!question || chatLoading) return;
    setLandingInput('');
    void sendMessage(question);
  };

  if (!isInitialLoadComplete) {
    return null;
  }

  if (!hasContent) {
    return (
      <div className="empty-state">
         <div className="sidebar-uploader-wrap">
          <DocumentUploader documents={documents} onUpload={uploadDocument} uploadingFilename={uploadingFilename} />
        </div>

        <h1 className="empty-title">Chat With Your Docs</h1>
        <p className="empty-subtitle">Upload a document and ask anything about it.</p>
        <AnimatedInput
          value={landingInput}
          onChange={setLandingInput}
          onSubmit={handleLandingSubmit}
          disabled={chatLoading}
        />
        {chatError && <p className="empty-error">{chatError}</p>}
      </div>
    );
  }

  return (
    <div className="app-active">
      <aside className="sidebar">
        <h1 className="sidebar-title">Chat With Your Docs</h1>

        <div className="sidebar-uploader-wrap">
          <DocumentUploader documents={documents} onUpload={uploadDocument} uploadingFilename={uploadingFilename} />
        </div>

        {documentsError && <p className="sidebar-error">{documentsError}</p>}

        <div className="sidebar-documents">
          <h2 className="sidebar-section-label">Documents</h2>
          <DocumentList documents={documents} isLoading={documentsLoading} onDelete={deleteDocument} />
        </div>
      </aside>

      <main className="main-area">
        <ChatInterface messages={messages} isLoading={chatLoading} error={chatError} onSend={sendMessage} />
      </main>
    </div>
  );
}

export default App;
