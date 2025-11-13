import ChatPageContent from "./[chatId]/ChatPageContent";

type ChatRootPageProps = {
  searchParams?: Record<string, string | string[] | undefined>;
};

export default async function ChatRootPage({ searchParams }: ChatRootPageProps) {
  const rawMessage = await searchParams?.message;
  const message =
    typeof rawMessage === "string"
      ? rawMessage
      : Array.isArray(rawMessage)
      ? rawMessage[0]
      : undefined;

  const trimmedMessage = message?.trim();

  return (
    <ChatPageContent
      initialMessage={trimmedMessage && trimmedMessage.length > 0 ? trimmedMessage : undefined}
    />
  );
}

