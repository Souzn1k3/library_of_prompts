import type { Metadata } from "next";

import { ApiRequestError } from "@/lib/api";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getTranslation } from "@/lib/i18n";
import { buildPageMetadata } from "@/lib/seo";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

import { MyLearningModulesView } from "./MyLearningModulesView";
import { loadMyLearningPageData } from "./my-learning-page-data";

export const revalidate = 0;

export async function generateMetadata(): Promise<Metadata> {
  const language = await getServerLanguage();
  return buildPageMetadata({
    title: `${getTranslation(language, "nav.learn")} · ${getTranslation(language, "learn.myModules")}`,
    description: getTranslation(language, "learn.myModulesDescription"),
    path: APP_ROUTES.learnMy,
  });
}

export default async function MyLearningModulesPage() {
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();

  try {
    const data = await loadMyLearningPageData({ accessToken, language });
    return <MyLearningModulesView language={language} data={data} />;
  } catch (error) {
    const message =
      error instanceof ApiRequestError ? error.message : getTranslation(language, "learn.loadFailed");
    return <div className="pv-page-sm"><div className="pv-alert pv-alert-warning">{message}</div></div>;
  }
}
