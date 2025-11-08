import ChatPageContent from "./ChatPageContent";

type ChatPageProps = {
  params: {
    chatId: string;
  };
};

export default async function ChatPage({ params }: ChatPageProps) {
  const { chatId } = await params;
  return <ChatPageContent chatId={chatId} />;
}
