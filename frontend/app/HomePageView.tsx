import { JsonLd } from "@/components/seo/JsonLd";
import { absoluteUrl } from "@/lib/seo";

import { HomeHeroSection } from "./HomeHeroSection";
import { HomeScenariosSection } from "./HomeScenariosSection";
import type { HomePageData } from "./home-page-data";

type HomePageViewProps = {
  initialAuthenticated: boolean;
  data: HomePageData;
};

export function HomePageView({ initialAuthenticated, data }: HomePageViewProps) {
  const {
    entryPrompts,
    recommendedPrompts,
    packs,
    chains,
    nextSteps,
    returnTriggers,
    showcase,
    pricingPlans,
    heroPromptBody,
    quickUseCases,
    retentionPrompts,
  } = data;
  const scenarioPrompts = recommendedPrompts.length ? recommendedPrompts : entryPrompts;

  return (
    <div className="pv-page">
      <JsonLd
        id="ld-home-growth-surfaces"
        data={{
          "@context": "https://schema.org",
          "@type": "WebPage",
          name: "Prompts Vault",
          url: absoluteUrl("/"),
          mainEntity: {
            "@type": "ItemList",
            itemListElement: scenarioPrompts.slice(0, 6).map((prompt, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: prompt.title,
              url: absoluteUrl(`/prompt/${prompt.slug}`),
            })),
          },
        }}
      />

      <HomeHeroSection
        entryPrompts={entryPrompts}
        heroPromptBody={heroPromptBody}
        quickUseCases={quickUseCases}
      />

      <HomeScenariosSection
        prompts={entryPrompts}
        recommendedPrompts={recommendedPrompts}
        retentionPrompts={retentionPrompts}
        packs={packs}
        chains={chains}
        nextSteps={nextSteps}
        returnTriggers={returnTriggers}
        showcase={showcase}
        pricingPlans={pricingPlans}
        initialAuthenticated={initialAuthenticated}
      />
    </div>
  );
}
