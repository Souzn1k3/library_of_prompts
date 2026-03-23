import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-12">
      <section className="space-y-6" aria-labelledby="hero-heading">
        <p className="text-xs font-medium uppercase tracking-widest text-zinc-500">
          Prompt engineering library
        </p>
        <h1
          id="hero-heading"
          className="max-w-2xl text-3xl font-semibold tracking-tight text-zinc-900 sm:text-4xl"
        >
          Use AI effectively with structured, high-quality prompts.
        </h1>
        <p className="max-w-2xl text-lg leading-relaxed text-zinc-600">
          Prompts Vault is a professional catalog of prompts and techniques—from zero-shot to
          chain-of-thought—organized for learning and real tasks.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link
            href="/catalog"
            className="inline-flex items-center justify-center rounded-md bg-zinc-900 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800"
          >
            Browse catalog
          </Link>
          <Link
            href="/learn"
            className="inline-flex items-center justify-center rounded-md border border-zinc-300 bg-white px-4 py-2.5 text-sm font-medium text-zinc-900 transition hover:border-zinc-400"
          >
            Start learning
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center justify-center rounded-md border border-zinc-300 bg-white px-4 py-2.5 text-sm font-medium text-zinc-900 transition hover:border-zinc-400"
          >
            Create account
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3" aria-label="Product highlights">
        {[
          {
            title: "Structured library",
            body: "Categories, techniques, and filters so you find the right pattern fast.",
          },
          {
            title: "Built to learn",
            body: "Education paths from beginner prompts to advanced workflows (rolling out).",
          },
          {
            title: "Serious tool",
            body: "Minimal UI, clear hierarchy—built for focus, not distraction.",
          },
        ].map((card) => (
          <div
            key={card.title}
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
