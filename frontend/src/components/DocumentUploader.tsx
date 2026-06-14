import { useRef, useState } from 'react';
import type { ChangeEvent, DragEvent } from 'react';
import type { DocumentInfo } from '../types';
import '../styles/uploader.css';

interface DocumentUploaderProps {
  documents: DocumentInfo[];
  onUpload: (file: File) => Promise<void>;
  uploadingFilename: string | null;
}

const ACCEPTED_EXTENSIONS = '.pdf,.docx,.txt';

/** Drag-and-drop (or click-to-browse) zone for uploading a PDF, DOCX, or TXT document. */
export function DocumentUploader({ documents, onUpload, uploadingFilename }: DocumentUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isUploading = uploadingFilename !== null;
  const lastUploaded = documents[documents.length - 1];

  const handleFile = (file: File | undefined) => {
    if (!file || isUploading) return;
    void onUpload(file);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    handleFile(event.dataTransfer.files[0]);
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFile(event.target.files?.[0]);
    event.target.value = '';
  };

  const triggerFileInput = () => {
    if (!isUploading) fileInputRef.current?.click();
  };

  return (
    <div
      className={`upload-container ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
      onDrop={handleDrop}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onClick={triggerFileInput}
      role="button"
      tabIndex={0}
    >
      <div className="folder">
        <div className="front-side">
          <div className="tip" />
          <div className="cover" />
        </div>
        <div className="back-side cover" />
      </div>
      <div className="upload-label">
        <p className="upload-main-text">
          {isUploading ? `Uploading ${uploadingFilename}…` : 'Drag & drop a document here'}
        </p>
        <p className="upload-sub-text">or click to browse</p>
        <p className="upload-types">PDF, DOCX, or TXT — max 20MB</p>
        {isUploading && (
          <div className="upload-progress">
            <div className="upload-progress-bar" />
          </div>
        )}
      </div>
      {!isUploading && lastUploaded && (
        <p className="upload-current-doc" title={lastUploaded.filename}>
          📄 {lastUploaded.filename}
        </p>
      )}
      <input
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        hidden
        ref={fileInputRef}
        onChange={handleFileChange}
        disabled={isUploading}
      />
    </div>
  );
}
