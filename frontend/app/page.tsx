import type { ReactNode } from "react";

import Link from "next/link";

import { HomeHeroSection } from "./HomeHeroSection";
import { loadHomePageData } from "./home-page-data";

import { PromptCard } from "@/components/PromptCard";
import { T } from "@/components/i18n/T";
import { JsonLd } from "@/components/seo/JsonLd";
import { DEFAULT_LANGUAGE } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";
import type { PromptListItem } from "@/lib/types";

export const dynamic = "force-static";
export const revalidate = 180;

export default async function HomePage() {
  const language = DEFAULT_LANGUAGE;

  const data = await loadHomePageData({
    accessToken: null,
    language,
  }).catch(() => ({
    entryPrompts: [],
    recommendedPrompts: [],
    retentionPrompts: [],
    heroPromptBody: null,
    quickUseCases: [],
  }));

  const featuredPrompts = data.recommendedPrompts.length
    ? data.recommendedPrompts
    : data.entryPrompts.slice(0, 6);

  return (
    <div className="pv-page space-y-6">
      <JsonLd
        id="ld-home-workbench"
        data={{
          "@context": "https://schema.org",
          "@type": "WebPage",
          name: "Prompts Vault",
          url: absoluteUrl("/"),
          mainEntity: {
            "@type": "ItemList",
            itemListElement: featuredPrompts.map((prompt, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: prompt.title,
              url: absoluteUrl(`/prompt/${prompt.slug}`),
            })),
          },
        }}
      />

      <HomeHeroSection
        entryPrompts={data.entryPrompts}
        heroPromptBody={data.heroPromptBody}
        quickUseCases={data.quickUseCases}
      />

      <section className="pv-panel px-6 py-6 sm:px-7">
        <SectionIntro
          kicker={<T k="home.proofKicker" />}
          title={<T k="home.proofTitle" />}
          description={<T k="home.proofSubtitle" />}
        />
        <div className="mt-5 grid gap-3 lg:grid-cols-3">
          <InsightCard title={<T k="home.structuredLibraryTitle" />} body={<T k="home.structuredLibraryBody" />} />
          <InsightCard title={<T k="home.builtToLearnTitle" />} body={<T k="home.builtToLearnBody" />} />
          <InsightCard title={<T k="home.seriousToolTitle" />} body={<T k="home.seriousToolBody" />} />
        </div>
      </section>

      <section className="pv-panel px-6 py-6 sm:px-7">
        <SectionIntro
          kicker={<T k="home.flowKicker" />}
          title={<T k="home.flowTitle" />}
          description={<T k="home.flowSubtitle" />}
        />
        <div className="mt-5 grid gap-3 lg:grid-cols-3">
          <ActionStepCard
            index={1}
            title={<T k="home.flowStepOneTitle" />}
            body={<T k="home.flowStepOneBody" />}
            href="/catalog"
            action={<T k="home.flowStepOneAction" />}
          />
          <ActionStepCard
            index={2}
            title={<T k="home.flowStepTwoTitle" />}
            body={<T k="home.flowStepTwoBody" />}
            href="#home-workbench"
            action={<T k="home.flowStepTwoAction" />}
          />
          <ActionStepCard
            index={3}
            title={<T k="home.flowStepThreeTitleGuest" />}
            body={<T k="home.flowStepThreeBodyGuest" />}
            href="/signup"
            action={<T k="home.flowStepThreeActionGuest" />}
          />
        </div>
      </section>

      {data.quickUseCases.length ? (
        <section className="pv-panel px-6 py-6 sm:px-7">
          <SectionIntro
            kicker={<T k="home.quickPathsKicker" />}
            title={<T k="home.quickPathsTitle" />}
            description={<T k="home.quickPathsSubtitle" />}
          />
          <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {data.quickUseCases.slice(0, 4).map((useCase) => (
              <Link
                key={`quick-path-${useCase}`}
                href={`/catalog?q=${encodeURIComponent(useCase)}`}
                className="pv-card block p-4"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                  <T k="home.quickPathsCardLabel" />
                </p>
                <h3 className="mt-3 text-lg font-semibold tracking-[-0.03em] text-zinc-950">{useCase}</h3>
                <p className="mt-2 text-sm leading-relaxed text-zinc-600">
                  <T k="home.quickPathsCardBody" params={{ useCase }} />
                </p>
                <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
                  <T k="home.quickPathsCardAction" />
                  <span aria-hidden="true">↗</span>
                </span>
              </Link>
            ))}
          </div>
        </section>
      ) : null}

      <section className="pv-panel px-6 py-6 sm:px-7">
        <SectionIntro
          kicker={<T k="home.pathKicker" />}
          title={<T k="home.pathTitle" />}
          description={<T k="home.pathSubtitle" />}
        />
        <div className="mt-5 grid gap-3 lg:grid-cols-3">
          <PathCard
            title={<T k="home.pathBeginnerTitle" />}
            body={<T k="home.pathBeginnerBody" />}
            href="/learn"
            action={<T k="home.pathBeginnerAction" />}
          />
          <PathCard
            title={<T k="home.pathPractitionerTitle" />}
            body={<T k="home.pathPractitionerBody" />}
            href="/catalog"
            action={<T k="home.pathPractitionerAction" />}
          />
          <PathCard
            title={<T k="home.pathLibraryTitleGuest" />}
            body={<T k="home.pathLibraryBodyGuest" />}
            href="/signup"
            action={<T k="home.pathLibraryActionGuest" />}
          />
        </div>
      </section>

      <PromptShelf
        title={<T k="home.trendingPrompts" />}
        href="/catalog"
        hrefLabel={<T k="home.seeAll" />}
        prompts={featuredPrompts}
        idPrefix="home-workflows"
      />
    </div>
  );
}

function SectionIntro({
  kicker,
  title,
  description,
}: {
  kicker: ReactNode;
  title: ReactNode;
  description: ReactNode;
}) {
  return (
    <div className="pv-section-head">
      <div className="pv-section-copy max-w-[46rem]">
        <p className="pv-kicker">{kicker}</p>
        <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h2>
        <p className="mt-2 text-sm leading-relaxed text-zinc-600">{description}</p>
      </div>
    </div>
  );
}

function InsightCard({ title, body }: { title: ReactNode; body: ReactNode }) {
  return (
    <article className="pv-card p-5">
      <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{title}</h3>
      <p className="mt-3 text-sm leading-relaxed text-zinc-600">{body}</p>
    </article>
  );
}

function ActionStepCard({
  index,
  title,
  body,
  href,
  action,
}: {
  index: number;
  title: ReactNode;
  body: ReactNode;
  href: string;
  action: ReactNode;
}) {
  return (
    <article className="pv-card p-5">
      <span className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[var(--pv-border)] bg-[var(--pv-brand-soft)] text-sm font-semibold text-[var(--pv-brand-strong)]">
        {index}
      </span>
      <h3 className="mt-4 text-lg font-semibold tracking-[-0.03em] text-zinc-950">{title}</h3>
      <p className="mt-2 text-sm leading-relaxed text-zinc-600">{body}</p>
      <Link href={href} className="pv-inline-link mt-4 inline-flex">
        {action}
        <span aria-hidden="true">↗</span>
      </Link>
    </article>
  );
}

function PathCard({
  title,
  body,
  href,
  action,
}: {
  title: ReactNode;
  body: ReactNode;
  href: string;
  action: ReactNode;
}) {
  return (
    <Link href={href} className="pv-card block p-5">
      <h3 className="text-lg font-semibold tracking-[-0.03em] text-zinc-950">{title}</h3>
      <p className="mt-3 text-sm leading-relaxed text-zinc-600">{body}</p>
      <span className="mt-4 inline-flex items-center gap-2 text-sm font-semibold text-[var(--pv-brand-strong)]">
        {action}
        <span aria-hidden="true">↗</span>
      </span>
    </Link>
  );
}

function PromptShelf({
  title,
  href,
  hrefLabel,
  prompts,
  idPrefix,
}: {
  title: ReactNode;
  href: string;
  hrefLabel: ReactNode;
  prompts: PromptListItem[];
  idPrefix: string;
}) {
  if (!prompts.length) return null;

  return (
    <section className="pv-panel px-6 py-5 sm:px-7">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          <p className="pv-kicker">
            <T k="catalog.prompts" />
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h2>
        </div>
        <Link href={href} className="pv-inline-link">
          {hrefLabel}
          <span aria-hidden="true">↗</span>
        </Link>
      </div>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {prompts.map((prompt) => (
          <PromptCard key={`${idPrefix}-${prompt.id}`} prompt={prompt} />
        ))}
      </div>
    </section>
  );
}
