import Link from "next/link";

import { T } from "@/components/i18n/T";
import { PromptCard } from "@/components/PromptCard";
import type { PromptListItem } from "@/lib/types";

type HomeShelfSectionProps = {
  title: string;
  href: string;
  hrefLabel: string;
  prompts: PromptListItem[];
  idPrefix: string;
};

export function HomeShelfSection({
  title,
  href,
  hrefLabel,
  prompts,
  idPrefix,
}: HomeShelfSectionProps) {
  if (!prompts.length) {
    return null;
  }

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker pv-home-section-kicker">
            <T k="catalog.prompts" />
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h2>
        </div>
        <Link href={href} className="pv-inline-link">
          {hrefLabel}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {prompts.map((prompt) => (
          <PromptCard key={`${idPrefix}-${prompt.id}`} prompt={prompt} />
        ))}
      </div>
    </section>
  );
}
