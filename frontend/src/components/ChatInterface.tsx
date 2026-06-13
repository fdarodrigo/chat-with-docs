import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import type { ChatMessage } from '../types';
import { MessageBubble } from './MessageBubble';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  onSend: (question: string) => Promise<void>;
}

/** Main chat area: scrollable message history plus an input box with a send button. */
export function ChatInterface({ messages, isLoading, error, onSend }: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const question = input.trim();
    if (!question || isLoading) return;
    setInput('');
    void onSend(question);
  };

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-center text-sm text-slate-400">
            <p>Upload a document on the left, then ask a question to get started.</p>
          </div>
        )}
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm text-slate-400 shadow-sm">
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      {error && <p className="px-6 pb-1 text-xs text-red-600">{error}</p>}
      <form onSubmit={handleSubmit} className="flex items-center gap-2 border-t border-slate-200 bg-white p-4">
        <input
          type="text"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask a question about your documents…"
          disabled={isLoading}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-slate-50"
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Send
        </button>
      </form>
    </div>
  );
}
