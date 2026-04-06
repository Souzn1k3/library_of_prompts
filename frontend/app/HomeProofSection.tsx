import { T } from "@/components/i18n/T";
import { languageToIntlLocale, type Language } from "@/lib/i18n";

import type { HomeProofMetrics } from "./home-page-data";

type HomeProofSectionProps = {
  language: Language;
  proof: HomeProofMetrics;
};

export function HomeProofSection({ language, proof }: HomeProofSectionProps) {
  const format = new Intl.NumberFormat(languageToIntlLocale(language), {
    maximumFractionDigits: 0,
  });

  const proofItems = [
    {
      id: "prompt-count",
      value: format.format(proof.promptCount),
      labelKey: "home.proofPromptCount",
    },
    {
      id: "save-copy",
      value: format.format(proof.totalSaves + proof.totalCopies),
      labelKey: "home.proofSaveAndCopy",
    },
    {
      id: "lesson-count",
      value: format.format(proof.lessonCount),
      labelKey: "home.proofLessonCount",
    },
    {
      id: "top-quality-score",
      value: proof.hasQualitySignals ? `${format.format(proof.topQualityScore)}/100` : "n/a",
      labelKey: "home.proofTopScore",
    },
  ];

  return (
    <section className="pv-panel px-6 py-5 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker pv-home-section-kicker">
            <T k="home.proofKicker" />
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            <T k="home.proofTitle" />
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            <T k="home.proofSubtitle" />
          </p>
        </div>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {proofItems.map((item) => (
          <div key={item.id} className="pv-proof-item">
            <p className="pv-proof-value">{item.value}</p>
            <p className="pv-proof-label">
              <T k={item.labelKey} />
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
