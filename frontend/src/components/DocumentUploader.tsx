import { useRef, useState } from 'react';
import type { ChangeEvent, DragEvent } from 'react';

interface DocumentUploaderProps {
  onUpload: (file: File) => Promise<void>;
  uploadingFilename: string | null;
}

const ACCEPTED_EXTENSIONS = '.pdf,.docx,.txt';

/** Drag-and-drop (or click-to-browse) zone for uploading a PDF, DOCX, or TXT document. */
export function DocumentUploader({ onUpload, uploadingFilename }: DocumentUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const isUploading = uploadingFilename !== null;

  const handleFile = (file: File | undefined) => {
    if (!file || isUploading) return;
    void onUpload(file);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    handleFile(event.dataTransfer.files[0]);
  };

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFile(event.target.files?.[0]);
    event.target.value = '';
  };

  return (
    <div>
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        role="button"
        tabIndex={0}
        className={`cursor-pointer rounded-lg border-2 border-dashed p-6 text-center transition-colors ${
          isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 hover:border-indigo-400'
        } ${isUploading ? 'pointer-events-none opacity-60' : ''}`}
      >
        <p className="text-sm font-medium text-slate-700">
          {isUploading ? `Uploading ${uploadingFilename}…` : 'Drag & drop a document here'}
        </p>
        <p className="mt-1 text-xs text-slate-500">or click to browse</p>
        <p className="mt-2 text-xs text-slate-400">PDF, DOCX, or TXT — max 20MB</p>
        {isUploading && (
          <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-200">
            <div className="h-full w-1/2 animate-pulse rounded-full bg-indigo-500" />
          </div>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        className="hidden"
        onChange={handleChange}
        disabled={isUploading}
      />
    </div>
  );
}
