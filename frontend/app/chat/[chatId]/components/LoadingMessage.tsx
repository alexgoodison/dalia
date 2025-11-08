export default function LoadingMessage() {
  return (
    <li className="flex justify-start">
      <div
        className={`max-w-[85%] rounded-3xl px-4 py-3 text-base leading-relaxed bg-transparent text-neutral-900 dark:text-white`}>
        <div className="flex items-center gap-2 text-base text-neutral-500 dark:text-neutral-400">
          <span className="h-2 w-2 animate-pulse rounded-full bg-neutral-500 dark:bg-neutral-300" />
          <span>Thinking…</span>
        </div>
      </div>
    </li>
  );
}
