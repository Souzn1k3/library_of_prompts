import { MissionDetailClient } from "@/components/MissionDetailClient";
import { ApiRequestError, fetchMissionBySlug } from "@/lib/api";
import { getTranslation } from "@/lib/i18n";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

type Props = {
  params: Promise<{ slug: string }>;
};

export default async function MissionDetailPage(props: Props) {
  const { slug } = await props.params;
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();
  let initialMission = null;
  let initialError: string | null = null;
  let initialSignedOut = false;

  if (!accessToken) {
    initialSignedOut = true;
  } else {
    try {
      initialMission = await fetchMissionBySlug(slug, accessToken, language);
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        initialSignedOut = true;
      } else {
        initialError =
          error instanceof ApiRequestError ? error.message : getTranslation(language, "missionDetail.loadFailed");
      }
    }
  }

  return (
    <div className="space-y-4">
      <MissionDetailClient
        slug={slug}
        initialMission={initialMission}
        initialError={initialError}
        initialSignedOut={initialSignedOut}
      />
    </div>
  );
}
