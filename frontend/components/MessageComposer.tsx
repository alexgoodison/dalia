"use client";

import { FormEvent } from "react";
import { FiArrowUpRight } from "react-icons/fi";

export function MessageComposer() {
  const placeholder =
    "Hey Dalia, can you review Tesla's latest earnings and how it compares to Rivian?";

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    // TODO: wire up backend request
  };

  return (
    <form
      className="flex w-full flex-col items-stretch gap-4 text-left"
      onSubmit={handleSubmit}>
      <div className="relative">
        <textarea
          id="message"
          className="h-40 w-full resize-none rounded-3xl border border-neutral-200 bg-white px-5 py-4 pr-20 text-base leading-relaxed text-neutral-900 shadow-inner outline-none transition-colors focus:border-neutral-900 focus:ring-2 focus:ring-neutral-900/10 dark:border-white/10 dark:bg-black/40 dark:text-white dark:focus:border-white"
          placeholder={placeholder}
        />
        <button
          type="submit"
          className="absolute bottom-5 right-3 flex h-8 w-8 items-center justify-center rounded-full bg-neutral-900 text-white transition-colors hover:bg-neutral-700 focus:outline-none dark:bg-white dark:text-black dark:hover:bg-neutral-200">
          <FiArrowUpRight className="h-5 w-5" aria-hidden />
          <span className="sr-only">Send message</span>
        </button>
      </div>
    </form>
  );
}
