import { useEffect, useRef, useState } from 'react';
import type { ChatMessage } from '../types';
import { AnimatedInput } from './AnimatedInput';
import { MessageBubble } from './MessageBubble';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  onSend: (question: string) => Promise<void>;
}

/** Main chat area: scrollable message history plus an animated input bar pinned to the bottom. */
export function ChatInterface({ messages, isLoading, error, onSend }: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = () => {
    const question = input.trim();
    if (!question || isLoading) return;
    setInput('');
    void onSend(question);
  };

  return (
    <>
      <div className="messages-area">
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && <div className="loading-card loading-dots">Thinking</div>}
        <div ref={bottomRef} />
      </div>
      {error && <p className="chat-error">{error}</p>}
      <div className="input-bar">
        <AnimatedInput value={input} onChange={setInput} onSubmit={handleSubmit} disabled={isLoading} wide />
      </div>
    </>
  );
}
