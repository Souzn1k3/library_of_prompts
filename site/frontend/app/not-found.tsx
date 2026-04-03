import Link from "next/link";

export default function NotFound() {
  return (
    <div className="space-y-4 py-16 text-center">
      <h1 className="text-2xl font-semibold text-zinc-900">Page not found</h1>
      <p className="text-sm text-zinc-600">The page you requested does not exist.</p>
      <Link href="/" className="text-sm font-medium text-zinc-900 underline">
        Go home
      </Link>
    </div>
  );
}
