import Link from "next/link";

import { TrackedUpgradeButton } from "@/components/analytics/TrackedUpgradeButton";
import { PageIntro } from "@/components/navigation/PageIntro";
import { TokenAmount } from "@/components/ui/TokenAmount";
import {
  getDifficultyTranslationKey,
  getOutputTypeTranslationKey,
  getTechniqueTranslationKey,
  getTranslation,
  type Language,
} from "@/lib/i18n";
import type { Category, PromptDetail } from "@/lib/types";

type PromptPageHeaderProps = {
  language: Language;
  prompt: PromptDetail;
  category: Category | undefined;
};

export function PromptPageHeader({ language, prompt, category }: PromptPageHeaderProps) {
  return (
    <PageIntro
      breadcrumbs={[
        { label: getTranslation(language, "nav.catalog"), href: "/catalog" },
        ...(category
          ? [
            {
              label: category.name,
              href: `/category/${encodeURIComponent(category.slug)}`,
            },
          ]
          : []),
        { label: prompt.title },
      ]}
      eyebrow={getTranslation(language, "prompt.sectionTitle")}
      title={prompt.title}
      description={prompt.summary ?? undefined}
    >
      <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-500">
        <span className="font-medium text-zinc-700">
          {getTranslation(language, getTechniqueTranslationKey(prompt.technique))}
        </span>
        {prompt.difficulty ? (
          <span>
            · {getTranslation(language, getDifficultyTranslationKey(prompt.difficulty))}
          </span>
        ) : null}
        {prompt.output_type ? (
          <span>
            · {getTranslation(language, getOutputTypeTranslationKey(prompt.output_type))}
          </span>
        ) : null}
        {category ? <span>· {category.name}</span> : null}
      </div>

      {prompt.body_locked && !prompt.price ? (
        <div className="pv-alert pv-alert-warning text-sm">
          <p>{getTranslation(language, "prompt.previewOnlyMessage")}</p>
          <div className="mt-4 flex flex-wrap gap-3">
            <TrackedUpgradeButton
              href="/pricing?tier=starter"
              page={`/prompt/${prompt.slug}`}
              feature="locked_prompt_cta"
              metadata={{
                prompt_id: prompt.id,
                prompt_slug: prompt.slug,
                target_tier: "starter",
              }}
              className="inline-flex pv-button-primary"
              label={getTranslation(language, "prompt.upgradeToUnlock")}
            />
            {prompt.unlock_offer ? (
              <Link href="/store" className="pv-button-secondary">
                <span>{getTranslation(language, "prompt.unlockWithLumens")}</span>
                <TokenAmount amount={prompt.unlock_offer.price} state="spent" />
              </Link>
            ) : null}
          </div>
          {prompt.unlock_offer ? (
            <p className="mt-3 text-xs text-amber-900/80">
              {prompt.unlock_offer.item_title}
            </p>
          ) : null}
        </div>
      ) : null}
    </PageIntro>
  );
}
