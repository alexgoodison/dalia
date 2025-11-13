"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";

import { MessageComposer } from "./MessageComposer";

export function HomeMessageComposer() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = useCallback(
    async (message: string) => {
      try {
        setIsSubmitting(true);
        setError(null);

        const trimmed = message.trim();
        if (!trimmed) {
          return;
        }

        const params = new URLSearchParams({ message: trimmed });
        router.push(`/chat?${params.toString()}`);
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
    [router]
  );

  return (
    <MessageComposer onSubmit={handleSubmit} isSubmitting={isSubmitting} errorMessage={error} />
  );
}
