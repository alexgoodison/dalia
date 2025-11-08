"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";

import { postChatChatPost } from "../lib/api/client";
import type { ChatResponse } from "../lib/api/model";
import { MessageComposer } from "./MessageComposer";

export function HomeMessageComposer() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResponse = useCallback(
    (response: ChatResponse) => {
      if (!response?.conversation_id) {
        return;
      }

      router.push(`/chat/${response.conversation_id}`);
    },
    [router]
  );

  const handleSubmit = useCallback(
    async (message: string) => {
      try {
        setIsSubmitting(true);
        setError(null);

        const response = await postChatChatPost({ message });
        handleResponse(response.data);
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message);
          throw err;
        }

        setError("Unable to start a new chat.");
        throw err as Error;
      } finally {
        setIsSubmitting(false);
      }
    },
    [handleResponse]
  );

  return (
    <MessageComposer onSubmit={handleSubmit} isSubmitting={isSubmitting} errorMessage={error} />
  );
}
