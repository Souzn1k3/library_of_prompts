import { PromptCard } from "@/components/PromptCard";
import { getTranslation, type Language } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

type PromptRelatedSectionProps = {
  language: Language;
  related: PromptListItem[];
};

export function PromptRelatedSection({ language, related }: PromptRelatedSectionProps) {
  if (!related.length) {
    return null;
  }

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker">{getTranslation(language, "prompt.relatedScenarios")}</p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {getTranslation(language, "prompt.relatedScenarios")}
          </h2>
        </div>
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        {related.map((item) => (
          <PromptCard key={item.id} prompt={item} />
        ))}
      </div>
    </section>
  );
}
