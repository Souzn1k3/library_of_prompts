import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiRequestError, fetchLessonBySlug } from "@/lib/api";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  try {
    const lesson = await fetchLessonBySlug(slug);
    return { title: lesson.title, description: lesson.title };
  } catch {
    return { title: "Lesson" };
  }
}

export default async function LessonPage(props: Props) {
  const { slug } = await props.params;

  try {
    const lesson = await fetchLessonBySlug(slug);
    return (
      <article className="space-y-6">
        <Link href="/learn" className="text-xs font-medium text-zinc-500 hover:text-zinc-800">
          ← All lessons
        </Link>
        <header className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">{lesson.title}</h1>
          <p className="text-xs text-zinc-500">
            Minimum tier: {lesson.min_tier}
            {lesson.body_locked ? " · preview only" : ""}
          </p>
        </header>
        <pre className="whitespace-pre-wrap rounded-lg border border-zinc-200 bg-zinc-50 p-4 text-sm leading-relaxed text-zinc-900">
          {lesson.body}
        </pre>
      </article>
    );
  } catch (e) {
    if (e instanceof ApiRequestError && e.status === 404) {
      notFound();
    }
    return (
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        Could not load lesson.
      </div>
    );
  }
}
