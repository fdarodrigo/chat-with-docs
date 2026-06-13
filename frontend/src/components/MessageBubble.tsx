import type { ChatMessage } from '../types';
import { SourceCitation } from './SourceCitation';

interface MessageBubbleProps {
  message: ChatMessage;
}

/** A single chat message: user messages right-aligned, assistant messages left-aligned with sources. */
export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="message-row user">
        <div className="message-user">{message.content}</div>
      </div>
    );
  }

  return (
    <div className="message-row assistant">
      <div className="message-assistant">
        <span className="assistant-label">● Assistant</span>
        {message.content}
      </div>
      {message.sources && message.sources.length > 0 && (
        <div className="sources-list">
          {message.sources.map((source, index) => (
            <SourceCitation key={`${source.filename}-${source.page}-${index}`} source={source} />
          ))}
        </div>
      )}
    </div>
  );
}
