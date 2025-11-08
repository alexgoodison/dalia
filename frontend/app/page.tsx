import { MessageComposer } from "../components/MessageComposer";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-linear-to-b from-neutral-50 via-white to-neutral-100 px-6 py-16 font-sans dark:from-black dark:via-zinc-900 dark:to-black">
      <main className="p-8 flex w-full max-w-3xl flex-col items-center gap-10 rounded-3xl text-center">
        <div className="flex flex-col items-center gap-3">
          <h1 className="text-5xl font-semibold tracking-tight text-neutral-900 dark:text-white">
            dalia
          </h1>
        </div>
        <MessageComposer />
      </main>
    </div>
  );
}
