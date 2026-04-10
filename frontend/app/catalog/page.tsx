import type { Metadata } from "next";

import { DEFAULT_LANGUAGE, getTranslation } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";

import { CatalogPageView } from "./CatalogPageView";
import { loadCatalogPageData, parseCatalogQuery } from "./catalog-page-data";

export async function generateMetadata(): Promise<Metadata> {
  const language = DEFAULT_LANGUAGE;
  return buildPageMetadata({
    title: getTranslation(language, "meta.catalogTitle"),
    description: getTranslation(language, "meta.catalogDescription"),
    path: "/catalog",
  });
}

export const revalidate = 60;

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

export default async function CatalogPage({ searchParams }: PageProps) {
  const language = DEFAULT_LANGUAGE;
  const query = parseCatalogQuery((await searchParams) ?? {});
  const data = await loadCatalogPageData({ query, language });

  return <CatalogPageView language={language} data={data} />;
}
