"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import type { AxiosResponse } from "axios";

import { useChatSender, type ChatStreamEvent } from "../../../lib/chat/useChatSender";
import type { ChatMessageModel, ChatResponse } from "../../../lib/api/model";
import {
  getGetChatChatConversationIdGetQueryKey,
  useGetChatChatConversationIdGet,
} from "../../../lib/api/client";
import LoadingMessage from "./components/LoadingMessage";
import AssistantMessage from "./components/AssistantMessage";
import UserMessage from "./components/UserMessage";
import { MessageComposer } from "../../../components/MessageComposer";

type ChatPageContentProps = {
  chatId?: string;
  initialMessage?: string;
};

const ADDITIONAL_INFORMATION_REGEX =
  /<additional_information>[\s\S]*?<\/additional_information>/gi;

function stripAdditionalInformation(content?: string | null) {
  return content ? content.replace(ADDITIONAL_INFORMATION_REGEX, "").trim() : "";
}

export default function ChatPageContent({ chatId, initialMessage }: ChatPageContentProps) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const messageListRef = useRef<HTMLUListElement | null>(null);
  const hasAutoSentInitialMessage = useRef(false);

  const [optimisticMessages, setOptimisticMessages] = useState<
    Array<ChatMessageModel & { pending?: boolean }>
  >([]);
  const [streamError, setStreamError] = useState<string | null>(null);

  const pendingQueryKey = useMemo(() => ["/chat/pending"] as const, []);
  const initialConversationId = chatId && chatId !== "new" ? chatId : undefined;
  const {
    conversationId: activeConversationId,
    sendMessage: sendChatMessage,
    isSending,
    error: senderError,
    clearError,
  } = useChatSender(initialConversationId);
  const effectiveConversationId = activeConversationId ?? initialConversationId;

  const queryKey = useMemo(
    () =>
      effectiveConversationId
        ? getGetChatChatConversationIdGetQueryKey(effectiveConversationId)
        : pendingQueryKey,
    [effectiveConversationId, pendingQueryKey]
  );

  const { data, isLoading, isError, error, refetch, isFetching } =
    useGetChatChatConversationIdGet(effectiveConversationId ?? "", {
      query: {
        enabled: !!effectiveConversationId,
        queryKey,
      },
    });

  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [optimisticMessages, data]);

  const handleBeforeSend = useCallback(
    (content: string) => {
      setStreamError(null);
      clearError();
      setOptimisticMessages([
        { role: "user", content },
        { role: "assistant", content: "", pending: true },
      ]);
    },
    [clearError]
  );

  const handleSendError = useCallback((message?: string) => {
    setOptimisticMessages([]);
    setStreamError(message ?? "We couldn't send your message. Please try again.");
  }, []);

  const handleResponse = useCallback(
    (response: ChatResponse) => {
      setStreamError(null);
      setOptimisticMessages([]);
      const responseQueryKey = getGetChatChatConversationIdGetQueryKey(
        response.conversation_id
      );
      queryClient.setQueryData<AxiosResponse<ChatResponse> | undefined>(
        responseQueryKey,
        (existing) => {
          if (!existing) {
            return {
              data: response,
              status: 200,
              statusText: "OK",
              headers: {},
              config: {},
            } as AxiosResponse<ChatResponse>;
          }

          return { ...existing, data: response };
        }
      );
    },
    [queryClient]
  );

  const handleStreamEvent = useCallback(
    (event: ChatStreamEvent) => {
      if (event.type === "start") {
        setStreamError(null);
        clearError();
        return;
      }

      if (event.type === "content") {
        setOptimisticMessages((previous) => {
          if (previous.length === 0) {
            return [{ role: "assistant", content: event.chunk, pending: true }];
          }

          const next = [...previous];
          const assistantIndex = next.findIndex((item) => item.role === "assistant");
          if (assistantIndex === -1) {
            next.push({ role: "assistant", content: event.chunk, pending: true });
            return next;
          }

          const assistantMessage = next[assistantIndex];
          next[assistantIndex] = {
            ...assistantMessage,
            content: `${assistantMessage.content ?? ""}${event.chunk}`,
            pending: true,
          };

          return next;
        });
        return;
      }

      if (event.type === "error") {
        handleSendError(event.error);
      }
    },
    [clearError, handleSendError]
  );

  const handleSendMessage = useCallback(
    async (content: string) => {
      await sendChatMessage(content, {
        onBeforeSend: handleBeforeSend,
        onStreamEvent: handleStreamEvent,
        onResponse: handleResponse,
        onError: handleSendError,
      });
    },
    [handleBeforeSend, handleResponse, handleSendError, handleStreamEvent, sendChatMessage]
  );

  useEffect(() => {
    if (!initialMessage || initialConversationId || hasAutoSentInitialMessage.current) {
      return;
    }

    hasAutoSentInitialMessage.current = true;
    void handleSendMessage(initialMessage);
  }, [handleSendMessage, initialConversationId, initialMessage]);

  useEffect(() => {
    if (chatId || !initialMessage) {
      return;
    }

    if (activeConversationId) {
      router.replace(`/chat/${activeConversationId}`, { scroll: false });
    }
  }, [activeConversationId, chatId, initialMessage, router]);

  const handleStartNewChat = () => {
    router.push("/");
  };

  const combinedMessages = useMemo(() => {
    const serverMessages = data?.data?.messages ?? [];
    return [...serverMessages, ...optimisticMessages];
  }, [data, optimisticMessages]);

  return (
    <div className="flex min-h-screen flex-col bg-neutral-50 px-4 pb-10 pt-10 font-sans text-neutral-900 transition-colors dark:bg-black dark:text-white sm:px-6 lg:px-8">
      <main className="relative mx-auto flex w-full max-w-4xl flex-1 flex-col">
        <header className="flex flex-col gap-2 px-1 sm:flex-row sm:items-center sm:justify-between">
          <Link href="/">
            <h1 className="text-2xl font-semibold tracking-tight hover:underline">
              dalia: chat
            </h1>
          </Link>
          <button
            type="button"
            onClick={handleStartNewChat}
            className="self-start rounded-full border border-neutral-200 px-4 py-2 text-sm font-medium transition hover:bg-neutral-100 focus:outline-none focus:ring-2 focus:ring-neutral-400 focus:ring-offset-2 dark:border-neutral-700 dark:hover:bg-neutral-800 dark:focus:ring-neutral-600 dark:focus:ring-offset-zinc-900">
            Start new chat
          </button>
        </header>

        <section className="relative mt-6 flex flex-1 flex-col">
          {isLoading ? (
            <div className="flex flex-1 items-center justify-center text-sm text-neutral-500 dark:text-neutral-400">
              Loading conversation…
            </div>
          ) : isError ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
              <p className="text-sm text-red-600 dark:text-red-400">
                We couldn&apos;t load this conversation.
              </p>
              <p className="text-xs text-red-500 dark:text-red-300">
                {error instanceof Error ? error.message : "Unknown error"}
              </p>
              <button
                type="button"
                onClick={() => refetch()}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:focus:ring-offset-zinc-900">
                Try again
              </button>
            </div>
          ) : combinedMessages.length === 0 ? (
            <div className="flex flex-1 items-center justify-center text-sm text-neutral-500 dark:text-neutral-400">
              This conversation is empty. Send a message to get started.
            </div>
          ) : (
            <ul
              ref={messageListRef}
              className="flex flex-1 flex-col gap-4 overflow-y-auto pb-88 pr-1">
              {combinedMessages.map((item, index) => {
                if ("pending" in item && item.pending) {
                  return <LoadingMessage key={index} />;
                }

                const cleanedContent = stripAdditionalInformation(item.content);

                switch (item.role) {
                  case "assistant":
                    return (
                      <AssistantMessage
                        key={index}
                        {...item}
                        content=""
                        optimisticContent={cleanedContent}
                      />
                    );
                  case "user":
                    return <UserMessage key={index} {...item} content={cleanedContent} />;
                  default:
                    return null;
                }
              })}
              {isFetching && (
                <li className="flex justify-center text-xs text-neutral-500 dark:text-neutral-400">
                  Updating…
                </li>
              )}
            </ul>
          )}
        </section>

        {(streamError || senderError) && (
          <div className="mx-auto mt-4 w-full max-w-3xl rounded-2xl border border-red-200 bg-red-50/80 px-2 py-3 text-sm text-red-700 dark:border-red-400/40 dark:bg-red-900/40 dark:text-red-200">
            {streamError || senderError}
          </div>
        )}

        <div className="pointer-events-none fixed bottom-0 left-0 right-0 w-full bg-linear-to-t from-neutral-50 via-neutral-50/90 to-transparent pb-4 dark:from-black dark:via-black/90">
          <div className="pointer-events-auto mx-auto w-full max-w-4xl px-1">
            <MessageComposer
              onSubmit={handleSendMessage}
              isSubmitting={isSending}
              errorMessage={streamError || senderError}
              placeholder="Ask Dalia anything about your finances, the market, or investing…"
            />
          </div>
        </div>
      </main>
    </div>
  );
}
