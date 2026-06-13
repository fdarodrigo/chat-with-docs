import { useState } from 'react';
import type { SourceCitation as SourceCitationType } from '../types';

interface SourceCitationProps {
  source: SourceCitationType;
}

/** Collapsible card showing a single retrieved source chunk used to ground an answer. */
export function SourceCitation({ source }: SourceCitationProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 text-xs">
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left font-medium text-slate-600 hover:text-indigo-600"
        aria-expanded={isOpen}
      >
        <span className="truncate">
          {source.filename} &middot; page {source.page} &middot; {(source.score * 100).toFixed(0)}% match
        </span>
        <span className="shrink-0 text-slate-400">{isOpen ? '−' : '+'}</span>
      </button>
      {isOpen && (
        <div className="border-t border-slate-200 px-3 py-2 text-slate-600">
          <p className="whitespace-pre-wrap">{source.text}</p>
        </div>
      )}
    </div>
  );
}
