import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-zinc-200 bg-zinc-50">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-3 px-4 py-8 text-sm text-zinc-600 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-zinc-500">© {new Date().getFullYear()} Prompts Vault</p>
        <div className="flex gap-6">
          <Link href="/catalog" className="transition hover:text-zinc-900">
            Browse prompts
          </Link>
          <Link href="/learn" className="transition hover:text-zinc-900">
            Learn
          </Link>
          <Link href="/plans" className="transition hover:text-zinc-900">
            Plans
          </Link>
        </div>
      </div>
    </footer>
  );
}
