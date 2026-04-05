"use client";

import Link from "next/link";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { appRoute } from "@/lib/constants/routes";
import type { MissionRead } from "@/lib/types";

type MissionDetailLinkedContentAsideProps = {
  mission: MissionRead;
};

export function MissionDetailLinkedContentAside({ mission }: MissionDetailLinkedContentAsideProps) {
  const { t } = useI18n();

  return (
    <aside className="space-y-4">
      {mission.prompts.length ? (
        <section className="pv-panel px-5 py-5">
          <p className="pv-kicker">{t("missionDetail.linkedPrompts")}</p>
          <ul className="mt-4 space-y-3 text-sm text-zinc-700">
            {mission.prompts.map((prompt) => (
              <li key={prompt.id} className="pv-card-muted p-3">
                <Link href={appRoute.promptBySlug(prompt.slug)} className="font-medium text-zinc-900 underline">
                  {prompt.title}
                </Link>
                {prompt.summary ? <p className="mt-1 text-zinc-600">{prompt.summary}</p> : null}
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {mission.lesson ? (
        <section className="pv-panel px-5 py-5">
          <p className="pv-kicker">{t("missionDetail.linkedLesson")}</p>
          <p className="mt-4 text-sm font-medium text-zinc-950">{mission.lesson.title}</p>
          <Link href={appRoute.learnBySlug(mission.lesson.slug)} className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
            {mission.lesson.locked ? `${t("missionDetail.locked")} · ${t("nav.plans")}` : t("learn.open")}
            <span aria-hidden="true">↗</span>
          </Link>
        </section>
      ) : null}
    </aside>
  );
}
