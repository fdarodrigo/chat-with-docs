import { useCallback, useState } from 'react';
import { ApiError, api } from '../services/api';
import type { ChatMessage, ConversationMessage } from '../types';

interface UseChatResult {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (question: string) => Promise<void>;
}

/** Manages the chat transcript and sends questions to the RAG backend. */
export function useChat(): UseChatResult {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed) return;

      const userMessage: ChatMessage = { id: crypto.randomUUID(), role: 'user', content: trimmed };
      const history: ConversationMessage[] = messages.map(({ role, content }) => ({ role, content }));

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setError(null);

      try {
        const response = await api.sendChatMessage({ question: trimmed, conversation_history: history });
        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
          tokens_used: response.tokens_used,
        };
        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Failed to get a response. Please try again.');
      } finally {
        setIsLoading(false);
      }
    },
    [messages],
  );

  return { messages, isLoading, error, sendMessage };
}
