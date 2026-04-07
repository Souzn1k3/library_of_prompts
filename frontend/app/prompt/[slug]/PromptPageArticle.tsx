import { PromptViewTracker } from "@/components/analytics/PromptViewTracker";
import { JsonLd } from "@/components/seo/JsonLd";
import { isOfficialTeamContributor } from "@/lib/contributors";
import { getTranslation, type Language } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";

import { PromptPageAside } from "./PromptPageAside";
import { PromptPageContentPanel } from "./PromptPageContentPanel";
import { PromptPageHeader } from "./PromptPageHeader";
import { PromptRelatedSection } from "./PromptRelatedSection";
import { PromptScenarioStage } from "./PromptScenarioStage";
import type { PromptPageData } from "./prompt-page-data";

type PromptPageArticleProps = {
  language: Language;
  data: PromptPageData;
};

export function PromptPageArticle({ language, data }: PromptPageArticleProps) {
  const { prompt, category, related, foundationsCourseTitle, foundationsCourseHref } = data;

  const isOfficialTeamAuthor = isOfficialTeamContributor(prompt.contributor_slug);
  const hasVerifiedTier = prompt.contributor_tier === "verified" || prompt.contributor_tier === "top";
  const shouldShowVerifiedBadge = isOfficialTeamAuthor || hasVerifiedTier;
  const verifiedBadgeLabel = isOfficialTeamAuthor
    ? getTranslation(language, "prompt.officialTeamBadge")
    : getTranslation(
      language,
      prompt.contributor_tier === "top" ? "contributorTier.top" : "contributorTier.verified",
    );
  const canShowCreatorProfileLink = Boolean(prompt.contributor_slug) && !isOfficialTeamAuthor;
  const interactionMetadata = {
    prompt_slug: prompt.slug,
    category_slug: category?.slug ?? null,
    contributor_slug: prompt.contributor_slug ?? null,
  };

  return (
    <article className="pv-page-sm">
      <PromptViewTracker
        promptId={prompt.id}
        promptSlug={prompt.slug}
        bodyLocked={Boolean(prompt.body_locked)}
        categorySlug={category?.slug ?? null}
        contributorSlug={prompt.contributor_slug ?? null}
      />

      <JsonLd
        id={`ld-prompt-${prompt.slug}`}
        data={{
          "@context": "https://schema.org",
          "@type": "CreativeWork",
          name: prompt.title,
          url: absoluteUrl(`/prompt/${prompt.slug}`),
          description: prompt.summary ?? prompt.title,
        }}
      />

      <PromptScenarioStage language={language} prompt={prompt} />

      <PromptPageHeader language={language} prompt={prompt} category={category} />

      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-start">
        <PromptPageContentPanel
          language={language}
          promptId={prompt.id}
          promptSlug={prompt.slug}
          body={prompt.body}
          bodyLocked={Boolean(prompt.body_locked)}
          interactionMetadata={interactionMetadata}
        />
        <PromptPageAside
          language={language}
          prompt={prompt}
          interactionMetadata={interactionMetadata}
          shouldShowVerifiedBadge={shouldShowVerifiedBadge}
          verifiedBadgeLabel={verifiedBadgeLabel}
          canShowCreatorProfileLink={canShowCreatorProfileLink}
          foundationsCourseTitle={foundationsCourseTitle}
          foundationsCourseHref={foundationsCourseHref}
        />
      </div>

      <PromptRelatedSection language={language} related={related} />
    </article>
  );
}
