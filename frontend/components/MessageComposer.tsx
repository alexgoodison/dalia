"use client";

import { FormEvent, KeyboardEvent, useCallback, useMemo, useState } from "react";
import { FiArrowUp } from "react-icons/fi";

interface MessageComposerProps {
  placeholder?: string;
  onSubmit: (message: string) => Promise<void>;
  isSubmitting?: boolean;
  errorMessage?: string | null;
}

export function MessageComposer({
  placeholder = "Hey Dalia, can you review Tesla's latest earnings and how it compares to Rivian?",
  onSubmit,
  isSubmitting = false,
  errorMessage,
}: MessageComposerProps) {
  const [message, setMessage] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);

  const isDisabled = useMemo(
    () => isSubmitting || message.trim().length === 0,
    [isSubmitting, message]
  );

  const submitMessage = useCallback(async () => {
    const trimmed = message.trim();
    if (trimmed.length === 0 || isSubmitting) {
      return;
    }

    try {
      await onSubmit(trimmed);
      setMessage("");
      setLocalError(null);
    } catch (err) {
      if (err instanceof Error) {
        setLocalError(err.message);
      } else {
        setLocalError("Unable to send your message.");
      }
    }
  }, [message, isSubmitting, onSubmit]);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      await submitMessage();
    },
    [submitMessage]
  );

  const handleKeyDown = useCallback(
    async (event: KeyboardEvent<HTMLTextAreaElement>) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        await submitMessage();
      }
    },
    [submitMessage]
  );

  const displayedError = errorMessage ?? localError;

  return (
    <form
      className="flex w-full flex-col items-stretch gap-4 text-left"
      onSubmit={handleSubmit}>
      <div className="relative">
        <textarea
          id="message"
          name="message"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSubmitting}
          className="h-40 w-full resize-none rounded-3xl border border-neutral-200 bg-white px-5 py-4 pr-20 text-base leading-relaxed text-neutral-900 shadow-inner outline-none transition-colors focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10 disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/10 dark:bg-black/40 dark:text-white dark:focus:border-white"
          placeholder={placeholder}
          minLength={1}
          required
        />
        <button
          type="submit"
          disabled={isDisabled}
          className="absolute bottom-5 right-3 flex h-8 w-8 items-center justify-center rounded-full bg-neutral-900 text-white transition-colors hover:bg-neutral-700 focus:outline-none disabled:cursor-not-allowed disabled:opacity-60 dark:bg-white dark:text-black dark:hover:bg-neutral-200">
          <FiArrowUp className="h-5 w-5" aria-hidden />
          <span className="sr-only">Send message</span>
        </button>
      </div>
      {displayedError && (
        <p className="text-sm text-red-600 dark:text-red-400" role="alert">
          {displayedError}
        </p>
      )}
    </form>
  );
}
