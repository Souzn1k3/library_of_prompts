"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { appRoute } from "@/lib/constants/routes";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { getMissionStatusTranslationKey } from "@/lib/i18n";
import type { MissionPresentation } from "@/lib/missionPresentation";

type MissionDetailStepsSectionProps = {
  missionView: MissionPresentation;
};

export function MissionDetailStepsSection({ missionView }: MissionDetailStepsSectionProps) {
  const { t } = useI18n();

  if (!missionView.steps.length) {
    return (
      <section className="pv-panel px-6 py-6 sm:px-7">
        <p className="pv-kicker">{t("missions.objective")}</p>
        <p className="mt-4 text-sm leading-relaxed text-zinc-700">{missionView.objective}</p>
      </section>
    );
  }

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <p className="pv-kicker">{t("missions.steps")}</p>
      <div className="mt-4 space-y-3">
        {missionView.steps.map((step, index) => (
          <div key={step.id} className="pv-card-muted p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                  {index + 1}. {t(getMissionStatusTranslationKey(step.status))}
                </p>
                <p className="text-base font-semibold text-zinc-950">{step.title}</p>
                {step.description ? <p className="text-sm text-zinc-600">{step.description}</p> : null}
              </div>
              <div className="text-right text-sm text-zinc-600">
                <p>
                  {step.progress_count}/{step.required_count}
                </p>
                {step.reward_credits > 0 ? (
                  <LmnAmount amount={`+${step.reward_credits}`} symbol={TOKEN_SHORT_CODE} state="earned" />
                ) : null}
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-3">
              {step.prompt ? (
                <Link href={appRoute.promptBySlug(step.prompt.slug)} className="pv-inline-link">
                  {step.prompt.title}
                </Link>
              ) : null}
              {step.lesson ? (
                <Link href={appRoute.learnBySlug(step.lesson.slug)} className="pv-inline-link">
                  {step.lesson.title}
                </Link>
              ) : null}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
