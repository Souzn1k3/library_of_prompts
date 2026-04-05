import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { formatTranslation, getTranslation, type Language } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

import { CategoryPageView } from "./CategoryPageView";
import { findCategoryBySlug, loadCategoryPageData } from "./category-page-data";

type Props = { params: Promise<{ slug: string }> };

export const revalidate = 300;

function buildCategoryFallbackMetadata(slug: string, language: Language): Metadata {
  return buildPageMetadata({
    title: getTranslation(language, "category.metadataFallbackTitle"),
    description: getTranslation(language, "category.metadataFallbackDescription"),
    path: `/category/${slug}`,
  });
}

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();
  const category = await findCategoryBySlug(slug, accessToken, language);
  if (!category) {
    return buildCategoryFallbackMetadata(slug, language);
  }
  return buildPageMetadata({
    title: formatTranslation(language, "category.metaTitle", { category: category.name }),
    description: formatTranslation(language, "category.metaDescription", { category: category.name }),
    path: `/category/${category.slug}`,
  });
}

export default async function CategoryPage(props: Props) {
  const { slug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  const category = await findCategoryBySlug(slug, accessToken, language);
  if (!category) {
    notFound();
  }

  const data = await loadCategoryPageData({ category, accessToken, language });
  if (!data.trending.length) {
    notFound();
  }

  return <CategoryPageView language={language} data={data} />;
}
