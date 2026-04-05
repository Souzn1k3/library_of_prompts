import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { formatTranslation, getTranslation, type Language } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

import { CategoryIntentPageView } from "./CategoryIntentPageView";
import { loadCategoryIntentPageData, resolveCategoryIntentLanding } from "./category-intent-page-data";

type Props = { params: Promise<{ slug: string; intentSlug: string }> };

export const revalidate = 300;

function buildCategoryIntentFallbackMetadata(
  slug: string,
  intentSlug: string,
  language: Language,
): Metadata {
  return buildPageMetadata({
    title: getTranslation(language, "categoryIntent.metadataFallbackTitle"),
    description: getTranslation(language, "categoryIntent.metadataFallbackDescription"),
    path: `/category/${slug}/intent/${intentSlug}`,
  });
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug, intentSlug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();
  const { current } = await resolveCategoryIntentLanding(slug, intentSlug, accessToken, language);
  if (!current) {
    return buildCategoryIntentFallbackMetadata(slug, intentSlug, language);
  }
  return buildPageMetadata({
    title: formatTranslation(language, "categoryIntent.metaTitle", {
      intent: current.intent_name,
      category: current.category_name,
    }),
    description: formatTranslation(language, "categoryIntent.metaDescription", {
      intent: current.intent_name,
      category: current.category_name,
    }),
    path: `/category/${current.category_slug}/intent/${current.intent_slug}`,
  });
}

export default async function CategoryIntentPage(props: Props) {
  const { slug, intentSlug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  const { current, siblings } = await resolveCategoryIntentLanding(slug, intentSlug, accessToken, language);
  if (!current) {
    notFound();
  }

  const data = await loadCategoryIntentPageData({
    current,
    siblings,
    accessToken,
    language,
  });

  if (data.prompts.length < 2) {
    notFound();
  }

  return <CategoryIntentPageView language={language} data={data} />;
}
