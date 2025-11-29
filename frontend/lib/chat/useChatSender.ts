import { useCallback, useState } from "react";

import type { ChatResponse } from "../api/model";
import { usePostChatChatPost } from "../api/client";

type SendMessageOptions = {
  conversationId?: string;
  onBeforeSend?: (message: string) => void;
  onResponse?: (response: ChatResponse) => void;
  onError?: (errorMessage: string) => void;
};

export function useChatSender(initialConversationId?: string) {
  const [conversationId, setConversationId] = useState<string | undefined>(
    initialConversationId
  );
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const { mutateAsync: sendChatRequest, isPending: isSending } = usePostChatChatPost();

  const sendMessage = useCallback(
    async (message: string, options: SendMessageOptions = {}) => {
      const {
        conversationId: providedConversationId,
        onBeforeSend,
        onResponse,
        onError,
      } = options;

      const trimmed = message.trim();
      if (!trimmed) {
        return;
      }

      try {
        setError(null);
        onBeforeSend?.(trimmed);

        const effectiveConversationId = providedConversationId ?? conversationId;

        const response = await sendChatRequest({
          data: {
            message: trimmed,
            conversation_id: effectiveConversationId ?? undefined,
          },
        });

        const chatResponse = response.data;
        setConversationId(chatResponse.conversation_id);
        onResponse?.(chatResponse);
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Something went wrong while sending your message.";
        setError(message);
        onError?.(message);
        throw err;
      }
    },
    [conversationId, sendChatRequest]
  );

  return {
    conversationId,
    setConversationId,
    sendMessage,
    isSending,
    error,
    clearError,
  };
}
