import { HomePageView } from "./HomePageView";
import { loadHomePageData } from "./home-page-data";

import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

export const revalidate = 180;

export default async function HomePage() {
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();
  const data = await loadHomePageData({ accessToken, language });

  return (
    <HomePageView
      language={language}
      initialAuthenticated={Boolean(accessToken)}
      data={data}
    />
  );
}
