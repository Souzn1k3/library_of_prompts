import Link from "next/link";

import { T } from "@/components/i18n/T";
import type { PromptListItem } from "@/lib/types";

type HomePathsSectionProps = {
  initialAuthenticated: boolean;
  quickUseCases: string[];
  entryPrompts: PromptListItem[];
};

export function HomePathsSection({
  initialAuthenticated,
  quickUseCases,
  entryPrompts,
}: HomePathsSectionProps) {
  if (!quickUseCases.length) {
    return null;
  }

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker pv-home-section-kicker">
            <T k="home.quickPathsKicker" />
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            <T k="home.quickPathsTitle" />
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            <T k="home.quickPathsSubtitle" />
          </p>
        </div>
        <Link href={initialAuthenticated ? "/dashboard" : "/signup"} className="pv-inline-link">
          <T k={initialAuthenticated ? "home.quickPathsWorkspaceAuth" : "home.quickPathsWorkspaceGuest"} />
          <span aria-hidden="true">↗</span>
        </Link>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {quickUseCases.slice(0, 4).map((useCase) => (
          <article key={`home-scenario-${useCase}`} className="pv-path-card">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-zinc-500">
              <T k="home.quickPathsCardLabel" />
            </p>
            <h3 className="mt-2 text-lg font-semibold tracking-[-0.03em] text-zinc-950">
              {formatUseCaseLabel(useCase)}
            </h3>
            <p className="mt-2 text-sm leading-relaxed text-zinc-600">
              <T k="home.quickPathsCardBody" params={{ useCase: formatUseCaseLabel(useCase) }} />
            </p>
            <Link href={resolveUseCaseHref(entryPrompts, useCase)} className="pv-inline-link mt-4 w-fit text-sm">
              <T k="home.quickPathsCardAction" />
              <span aria-hidden="true">↗</span>
            </Link>
          </article>
        ))}
      </div>
    </section>
  );
}

function formatUseCaseLabel(useCase: string): string {
  return useCase
    .split(" ")
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(" ");
}

function resolveUseCaseHref(prompts: PromptListItem[], useCase: string): string {
  const normalizedUseCase = useCase.toLowerCase();
  const matchingPrompt = prompts.find((prompt) => {
    const searchable = [
      ...(prompt.use_cases ?? []),
      ...(prompt.tags ?? []),
      prompt.title,
      prompt.summary ?? "",
    ]
      .join(" ")
      .toLowerCase()
      .replace(/[_-]+/g, " ");
    return searchable.includes(normalizedUseCase);
  });

  if (matchingPrompt) {
    return `/prompt/${encodeURIComponent(matchingPrompt.slug)}`;
  }
  return `/catalog?q=${encodeURIComponent(useCase)}`;
}
