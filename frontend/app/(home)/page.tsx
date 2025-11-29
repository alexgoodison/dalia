import { BackendStatusTag } from "../../components/BackendStatusTag";
import { HomeMessageComposer } from "../../components/HomeMessageComposer";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-6 py-16 font-sans text-neutral-900 transition-colors dark:bg-black dark:text-white">
      <main className="p-8 flex w-full max-w-3xl flex-col items-center gap-10 rounded-3xl text-center">
        <div className="flex flex-col items-center gap-3">
          <h1 className="text-5xl font-semibold tracking-tight text-neutral-900 dark:text-white">
            dalia
          </h1>
        </div>
        <HomeMessageComposer />
        <BackendStatusTag />
      </main>
    </div>
  );
}
