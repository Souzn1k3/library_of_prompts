import { JsonLd } from "@/components/seo/JsonLd";
import { getTranslation, type Language } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";

import { HomeHeroSection } from "./HomeHeroSection";
import { HomePathsSection } from "./HomePathsSection";
import { HomeScenariosSection } from "./HomeScenariosSection";
import { HomeShelfSection } from "./HomeShelfSection";
import type { HomePageData } from "./home-page-data";

type HomePageViewProps = {
  language: Language;
  initialAuthenticated: boolean;
  data: HomePageData;
};

export function HomePageView({ language, initialAuthenticated, data }: HomePageViewProps) {
  const {
    entryPrompts,
    recommendedPrompts,
    promptsTitle,
    heroPromptBody,
    quickUseCases,
  } = data;
  const shelfPrompts = recommendedPrompts.length ? recommendedPrompts : entryPrompts;

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
            itemListElement: shelfPrompts.slice(0, 6).map((prompt, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: prompt.title,
              url: absoluteUrl(`/prompt/${prompt.slug}`),
            })),
          },
        }}
      />

      <HomeHeroSection
        initialAuthenticated={initialAuthenticated}
        entryPrompts={entryPrompts}
        heroPromptBody={heroPromptBody}
        quickUseCases={quickUseCases}
      />

      <HomeScenariosSection
        prompts={entryPrompts}
        initialAuthenticated={initialAuthenticated}
      />

      <HomeShelfSection
        title={promptsTitle}
        href="/catalog"
        hrefLabel={getTranslation(language, "home.seeAll")}
        prompts={shelfPrompts}
        idPrefix="home-recommended"
      />

      <HomePathsSection
        initialAuthenticated={initialAuthenticated}
        quickUseCases={quickUseCases}
        entryPrompts={entryPrompts}
      />
    </div>
  );
}
