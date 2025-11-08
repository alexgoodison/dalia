import type { ChatMessageModel } from "../../../../lib/api/model";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface AssistantMessageProps extends ChatMessageModel {
  optimisticContent?: string;
}

export default function AssistantMessage({
  content,
  optimisticContent,
}: AssistantMessageProps) {
  const displayContent = (content ?? "").trim() || optimisticContent || "*...*";

  return (
    <li className="flex justify-start">
      <div
        className={`max-w-[85%] rounded-3xl px-2 py-3 text-base leading-relaxed bg-transparent text-neutral-900 dark:text-white`}>
        <div className="prose prose-sm max-w-none text-left text-neutral-900 dark:prose-invert dark:text-white">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayContent}</ReactMarkdown>
        </div>
      </div>
    </li>
  );
}
