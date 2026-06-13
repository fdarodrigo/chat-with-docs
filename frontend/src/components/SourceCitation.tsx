import { useState } from 'react';
import type { SourceCitation as SourceCitationType } from '../types';

interface SourceCitationProps {
  source: SourceCitationType;
}

/** Collapsible card showing a single retrieved source chunk used to ground an answer. */
export function SourceCitation({ source }: SourceCitationProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="source-citation">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="source-citation-header"
        aria-expanded={isOpen}
      >
        <span className="source-citation-label">
          <span className="source-citation-icon">◆</span>
          {source.filename} &middot; page {source.page}
        </span>
        <span className="source-citation-score">
          {(source.score * 100).toFixed(0)}% match {isOpen ? '−' : '+'}
        </span>
      </button>
      {isOpen && <div className="source-citation-body">{source.text}</div>}
    </div>
  );
}
