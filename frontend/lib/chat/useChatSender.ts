import { useCallback, useState } from "react";

import { postChatChatPost } from "../api/client";
import type { ChatMessageModel, ChatResponse } from "../api/model";

export type ChatStreamEvent =
  | { type: "start"; conversation_id: string }
  | { type: "content"; chunk: string }
  | { type: "complete"; conversation_id: string; messages: ChatMessageModel[] }
  | { type: "error"; error?: string };

type SendMessageOptions = {
  conversationId?: string;
  onBeforeSend?: (message: string) => void;
  onStreamEvent?: (event: ChatStreamEvent) => void;
  onResponse?: (response: ChatResponse) => void;
  onError?: (errorMessage: string) => void;
  useStreaming?: boolean;
};

export function useChatSender(initialConversationId?: string) {
  const [conversationId, setConversationId] = useState<string | undefined>(
    initialConversationId
  );
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const sendMessage = useCallback(
    async (message: string, options: SendMessageOptions = {}) => {
      const {
        conversationId: providedConversationId,
        onBeforeSend,
        onStreamEvent,
        onResponse,
        onError,
        useStreaming = !!onStreamEvent,
      } = options;

      const trimmed = message.trim();
      if (!trimmed) {
        return;
      }

      try {
        setIsSending(true);
        setError(null);
        onBeforeSend?.(trimmed);

        const effectiveConversationId = providedConversationId ?? conversationId;

        if (!useStreaming) {
          const response = await postChatChatPost({
            message: trimmed,
            conversation_id: effectiveConversationId ?? undefined,
          });
          const payload = response.data;
          setConversationId(payload.conversation_id);
          onResponse?.(payload);
          return payload;
        }

        const baseUrl =
          process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";
        const response = await fetch(`${baseUrl}/chat/stream`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
          },
          body: JSON.stringify({
            message: trimmed,
            conversation_id: effectiveConversationId ?? undefined,
          }),
        });

        if (!response.ok || !response.body) {
          throw new Error("Unable to start streaming response.");
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let encounteredError = false;

        const processEvent = (rawEvent: string) => {
          const trimmedEvent = rawEvent.trim();
          if (!trimmedEvent) {
            return;
          }

          const dataLines = trimmedEvent
            .split("\n")
            .filter((line) => line.startsWith("data:"))
            .map((line) => line.replace(/^data:\s*/, ""));

          if (dataLines.length === 0) {
            return;
          }

          let payload: ChatStreamEvent;
          try {
            payload = JSON.parse(dataLines.join("\n")) as ChatStreamEvent;
          } catch {
            return;
          }

          if (payload.type === "start") {
            setConversationId(payload.conversation_id);
          } else if (payload.type === "error") {
            encounteredError = true;
            const message =
              payload.error ?? "Something went wrong while streaming your message.";
            setError(message);
            onError?.(message);
          } else if (payload.type === "complete") {
            setConversationId(payload.conversation_id);
            onResponse?.({
              conversation_id: payload.conversation_id,
              messages: payload.messages,
              latest_message:
                payload.messages?.length ?? 0
                  ? payload.messages[payload.messages.length - 1]
                  : undefined,
            });
          }

          onStreamEvent?.(payload);
        };

        const flushBuffer = (isFinal = false) => {
          let separatorIndex = buffer.indexOf("\n\n");
          while (separatorIndex !== -1) {
            const rawEvent = buffer.slice(0, separatorIndex);
            buffer = buffer.slice(separatorIndex + 2);
            processEvent(rawEvent);
            separatorIndex = buffer.indexOf("\n\n");
          }

          if (isFinal && buffer.trim().length > 0) {
            processEvent(buffer);
            buffer = "";
          }
        };

        try {
          while (true) {
            const { value, done } = await reader.read();
            if (done) {
              buffer += decoder.decode();
              flushBuffer(true);
              break;
            }

            buffer += decoder.decode(value, { stream: true });
            flushBuffer();

            if (encounteredError) {
              break;
            }
          }
        } finally {
          reader.releaseLock();
        }

        if (encounteredError) {
          throw new Error("Streaming failed.");
        }
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Something went wrong while sending your message.";
        setError(message);
        onError?.(message);
        throw err;
      } finally {
        setIsSending(false);
      }
    },
    [conversationId]
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
