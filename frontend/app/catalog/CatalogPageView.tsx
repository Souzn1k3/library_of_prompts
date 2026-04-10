import { CatalogFilters } from "@/components/CatalogFilters";
import { T } from "@/components/i18n/T";
import { LearningCourseFeedCard } from "@/components/LearningCourseFeedCard";
import { PageIntro } from "@/components/navigation/PageIntro";
import { PromptCard } from "@/components/PromptCard";
import { JsonLd } from "@/components/seo/JsonLd";
import { getTranslation, type Language } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";
import type { LearningCourseCard, PromptListItem } from "@/lib/types";

import type { CatalogPageData } from "./catalog-page-data";

type CatalogPageViewProps = {
  language: Language;
  data: CatalogPageData;
};

export function CatalogPageView({ language, data }: CatalogPageViewProps) {
  const { query, categories, prompts, recommendedCourses, discoveryFilters, sections, error } = data;
  const discoveryPrompts = sections.for_you?.length ? sections.for_you : sections.trending;
  const promptFeed = query.hasCustomFilters ? prompts : mergePromptLists(discoveryPrompts, prompts);
  const courseFeed = query.hasCustomFilters ? [] : recommendedCourses;
  const feedItems = buildUnifiedFeed(courseFeed, promptFeed);

  return (
    <div className="pv-page">
      <JsonLd
        id="ld-catalog"
        data={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          name: getTranslation(language, "meta.catalogTitle"),
          url: absoluteUrl("/catalog"),
          description: getTranslation(language, "meta.catalogDescription"),
          mainEntity: {
            "@type": "ItemList",
            itemListElement: prompts.slice(0, 20).map((prompt, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: prompt.title,
              url: absoluteUrl(`/prompt/${prompt.slug}`),
            })),
          },
        }}
      />

      <PageIntro
        className="!overflow-visible"
        breadcrumbs={[
          { label: getTranslation(language, "brand.name"), href: "/" },
          { label: getTranslation(language, "nav.catalog") },
        ]}
        eyebrow={<T k="catalog.title" />}
        title={<T k="catalog.title" />}
        titleClassName="text-2xl font-bold tracking-[-0.04em] sm:text-2xl"
        description={<T k="catalog.subtitle" />}
      >
        {!error ? (
          <div className="mt-3">
            <CatalogFilters
              categories={categories}
              discoveryFilters={discoveryFilters}
              initial={{
                q: query.q,
                category_id: query.category_id,
                technique: query.technique,
                difficulty: query.difficulty,
                output_type: query.output_type,
                sort: query.sort || "relevance",
                use_case: query.use_case,
                model: query.model,
                tag: query.tag,
              }}
            />
          </div>
        ) : null}
      </PageIntro>

      {error ? (
        <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-medium">
            <T k="catalog.unavailable" />
          </p>
          <p className="mt-1 text-amber-800">{error}</p>
        </div>
      ) : null}

      <section className="pv-panel px-6 py-6 sm:px-7">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">
              <T k={query.hasCustomFilters ? "catalog.prompts" : "catalog.discoveryForYou"} />
            </h2>
          </div>
        </div>

        {feedItems.length === 0 ? (
          <p className="mt-6 text-sm text-zinc-500">
            <T k="catalog.noPrompts" />
          </p>
        ) : (
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {feedItems.map((item) => (
              item.kind === "course" ? (
                <LearningCourseFeedCard key={`course-${item.course.slug}`} course={item.course} />
              ) : (
                <PromptCard key={`prompt-${item.prompt.id}`} prompt={item.prompt} />
              )
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

type CatalogFeedItem =
  | { kind: "course"; course: LearningCourseCard }
  | { kind: "prompt"; prompt: PromptListItem };

function mergePromptLists(primary: PromptListItem[], fallback: PromptListItem[]): PromptListItem[] {
  const seenIds = new Set<string>();
  const merged: PromptListItem[] = [];

  for (const prompt of [...primary, ...fallback]) {
    if (seenIds.has(prompt.id)) {
      continue;
    }
    seenIds.add(prompt.id);
    merged.push(prompt);
  }

  return merged;
}

function buildUnifiedFeed(courses: LearningCourseCard[], prompts: PromptListItem[]): CatalogFeedItem[] {
  const feed: CatalogFeedItem[] = [];
  const maxLength = Math.max(courses.length, prompts.length);

  for (let index = 0; index < maxLength; index += 1) {
    const course = courses[index];
    const prompt = prompts[index];

    if (course) {
      feed.push({ kind: "course", course });
    }
    if (prompt) {
      feed.push({ kind: "prompt", prompt });
    }
  }

  return feed;
}
