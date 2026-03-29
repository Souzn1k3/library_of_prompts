import Link from "next/link";

import { T } from "@/components/i18n/T";

export default function NotFound() {
  return (
    <div className="pv-hero mx-auto max-w-3xl space-y-4 px-6 py-16 text-center">
      <h1 className="text-3xl font-semibold tracking-[-0.05em] text-zinc-900">
        <T k="notFound.title" />
      </h1>
      <p className="text-sm text-zinc-600">
        <T k="notFound.body" />
      </p>
      <Link href="/" className="pv-button-primary !w-auto">
        <T k="notFound.home" />
      </Link>
    </div>
  );
}
