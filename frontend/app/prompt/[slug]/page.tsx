import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiRequestError } from "@/lib/api";
import { formatTranslation, getTranslation } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

import { PromptPageArticle } from "./PromptPageArticle";
import { getPromptBySlugCached, loadPromptPageData } from "./prompt-page-data";

type Props = { params: Promise<{ slug: string }> };

export async function generateMetadata(props: Props): Promise<Metadata> {
  const { slug } = await props.params;
  const accessToken = await getServerAccessToken();
  const language = await getServerLanguage();
  try {
    const prompt = await getPromptBySlugCached(slug, accessToken, language);
    return buildPageMetadata({
      title: prompt.title,
      description:
        prompt.summary ??
        formatTranslation(language, "prompt.metadataDescriptionFallback", { title: prompt.title }),
      path: `/prompt/${prompt.slug}`,
      type: "article",
    });
  } catch {
    return buildPageMetadata({
      title: getTranslation(language, "prompt.metadataFallbackTitle"),
      description: getTranslation(language, "meta.catalogDescription"),
      path: `/prompt/${slug}`,
    });
  }
}

export default async function PromptPage(props: Props) {
  const { slug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const data = await loadPromptPageData({ slug, accessToken, language });
    return <PromptPageArticle language={language} data={data} />;
  } catch (e) {
    if (e instanceof ApiRequestError && e.status === 404) {
      notFound();
    }
    return (
      <div className="pv-alert pv-alert-warning text-sm">
        <p className="font-medium">{getTranslation(language, "prompt.loadFailedTitle")}</p>
        <p className="mt-1 text-amber-800">
          {e instanceof ApiRequestError ? e.message : getTranslation(language, "prompt.unexpectedError")}
        </p>
        <Link href="/catalog" className="mt-3 inline-block text-amber-950 underline">
          {getTranslation(language, "prompt.returnToCatalog")}
        </Link>
      </div>
    );
  }
}
