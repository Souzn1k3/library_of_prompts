"use client";

import Link from "next/link";

import { PromptCard } from "@/components/PromptCard";
import { APP_ROUTES } from "@/lib/constants/routes";
import type { TranslationKey } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type DashboardSavedPromptsSectionProps = {
  items: PromptListItem[];
  t: Translate;
};

export function DashboardSavedPromptsSection({
  items,
  t,
}: DashboardSavedPromptsSectionProps) {
  return (
    <section id="saved" className="pv-panel pv-section-anchor px-6 py-6 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">
            {t("dashboard.savedPrompts")}
          </h2>
        </div>
        <span className="pv-workspace-status">{items.length}</span>
      </div>

      {items.length === 0 ? (
        <div className="pv-empty-state mt-6 text-sm text-zinc-600">
          {t("dashboard.emptyPrefix")}{" "}
          <Link href={APP_ROUTES.catalog} className="font-medium text-zinc-900 underline">
            {t("dashboard.emptyLink")}
          </Link>{" "}
          {t("dashboard.emptySuffix")}
        </div>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          {items.map((prompt) => (
            <PromptCard key={prompt.id} prompt={prompt} />
          ))}
        </div>
      )}
    </section>
  );
}
