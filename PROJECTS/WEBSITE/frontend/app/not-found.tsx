import Link from "next/link";

import { T } from "@/components/i18n/T";

export default function NotFound() {
  return (
    <div className="space-y-4 py-16 text-center">
      <h1 className="text-2xl font-semibold text-zinc-900">
        <T k="notFound.title" />
      </h1>
      <p className="text-sm text-zinc-600">
        <T k="notFound.body" />
      </p>
      <Link href="/" className="text-sm font-medium text-zinc-900 underline">
        <T k="notFound.home" />
      </Link>
    </div>
  );
}
