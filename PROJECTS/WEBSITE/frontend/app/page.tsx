import Link from "next/link";

import { T } from "@/components/i18n/T";

export default function HomePage() {
  return (
    <div className="space-y-12">
      <section className="space-y-6" aria-labelledby="hero-heading">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          <T k="home.kicker" />
        </p>
        <h1
          id="hero-heading"
          className="max-w-2xl text-3xl font-semibold tracking-tight text-zinc-900 sm:text-4xl"
        >
          <T k="home.title" />
        </h1>
        <p className="max-w-2xl text-lg leading-relaxed text-zinc-600">
          <T k="home.subtitle" />
        </p>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/catalog"
            className="inline-flex items-center justify-center rounded-md bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800"
          >
            <T k="home.browseCatalog" />
          </Link>
          <Link
            href="/learn"
            className="inline-flex items-center justify-center rounded-md border border-zinc-300 bg-white px-4 py-2.5 text-sm font-medium text-zinc-900 transition hover:border-zinc-400"
          >
            <T k="home.startLearning" />
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center justify-center rounded-md border border-zinc-300 bg-white px-4 py-2.5 text-sm font-medium text-zinc-900 transition hover:border-zinc-400"
          >
            <T k="home.createAccount" />
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3" aria-label="Product highlights">
        {[
          {
            id: "structured",
            title: <T k="home.structuredLibraryTitle" />,
            body: <T k="home.structuredLibraryBody" />,
          },
          {
            id: "learn",
            title: <T k="home.builtToLearnTitle" />,
            body: <T k="home.builtToLearnBody" />,
          },
          {
            id: "tool",
            title: <T k="home.seriousToolTitle" />,
            body: <T k="home.seriousToolBody" />,
          },
        ].map((card) => (
          <div
            key={card.id}
            className="rounded-lg border border-zinc-200 bg-zinc-50/60 p-5 shadow-card"
          >
            <h2 className="text-sm font-semibold text-zinc-900">{card.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">{card.body}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
