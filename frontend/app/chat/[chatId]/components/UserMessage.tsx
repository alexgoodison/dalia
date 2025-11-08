import type { ChatMessageModel } from "../../../../lib/api/model";

type UserMessageProps = ChatMessageModel;

export default function UserMessage({ content }: UserMessageProps) {
  return (
    <li className="flex justify-end">
      <div
        className={
          "max-w-[85%] rounded-3xl px-4 py-3 text-base leading-relaxed bg-neutral-100 text-right text-neutral-900 dark:bg-neutral-800/70 dark:text-white"
        }>
        <p
          className="whitespace-pre-wrap"
          style={{ overflowWrap: "break-word", wordBreak: "break-word" }}>
          {content}
        </p>
      </div>
    </li>
  );
}
