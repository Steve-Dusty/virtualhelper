import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-center py-32 px-16 bg-white dark:bg-black">
        <div className="flex flex-col items-center gap-6 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-black dark:text-zinc-50">
            LiveKit Video Conference
          </h1>
          <p className="max-w-md text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            Join a real-time video and audio room powered by LiveKit
          </p>
          <Link
            href="/room"
            className="mt-4 flex h-12 items-center justify-center gap-2 rounded-full bg-blue-600 hover:bg-blue-700 px-8 text-white font-medium transition-colors"
          >
            Join Room
          </Link>
        </div>
      </main>
    </div>
  );
}
