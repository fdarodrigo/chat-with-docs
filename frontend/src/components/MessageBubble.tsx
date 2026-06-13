import type { ChatMessage } from '../types';
import { SourceCitation } from './SourceCitation';

interface MessageBubbleProps {
  message: ChatMessage;
}

/** A single chat message: user messages right-aligned, assistant messages left-aligned with sources. */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className="max-w-2xl">
        <div
          className={
            isUser
              ? 'rounded-2xl bg-indigo-600 px-4 py-2 text-sm text-white shadow-sm'
              : 'rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-800 shadow-sm'
          }
        >
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-2 space-y-1.5">
            {message.sources.map((source, index) => (
              <SourceCitation key={`${source.filename}-${source.page}-${index}`} source={source} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
