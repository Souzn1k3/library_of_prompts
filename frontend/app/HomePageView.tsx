import { JsonLd } from "@/components/seo/JsonLd";
import { getTranslation, type Language } from "@/lib/i18n";
import { absoluteUrl } from "@/lib/seo";

import { HomeHeroSection } from "./HomeHeroSection";
import { HomeLessonsSection } from "./HomeLessonsSection";
import { HomeShelfSection } from "./HomeShelfSection";
import type { HomePageData } from "./home-page-data";

type HomePageViewProps = {
  language: Language;
  initialAuthenticated: boolean;
  data: HomePageData;
};

export function HomePageView({ language, initialAuthenticated, data }: HomePageViewProps) {
  const { featuredPrompts, promptsTitle, popularLessons, heroPrompt, heroPromptBody } = data;

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
            itemListElement: featuredPrompts.slice(0, 6).map((prompt, index) => ({
              "@type": "ListItem",
              position: index + 1,
              name: prompt.title,
              url: absoluteUrl(`/prompt/${prompt.slug}`),
            })),
          },
        }}
      />

      <HomeHeroSection
        language={language}
        initialAuthenticated={initialAuthenticated}
        heroPrompt={heroPrompt}
        heroPromptBody={heroPromptBody}
      />

      <HomeShelfSection
        title={promptsTitle}
        href="/catalog"
        hrefLabel={getTranslation(language, "home.seeAll")}
        prompts={featuredPrompts}
        idPrefix="home-featured"
      />

      <HomeLessonsSection language={language} lessons={popularLessons} />
    </div>
  );
}
