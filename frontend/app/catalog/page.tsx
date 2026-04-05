import type { Metadata } from "next";

import { getTranslation } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

import { CatalogPageView } from "./CatalogPageView";
import { loadCatalogPageData, parseCatalogQuery } from "./catalog-page-data";

export async function generateMetadata(): Promise<Metadata> {
  const language = await getServerLanguage();
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
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();
  const query = parseCatalogQuery((await searchParams) ?? {});
  const data = await loadCatalogPageData({ query, accessToken, language });

  return <CatalogPageView language={language} data={data} />;
}
