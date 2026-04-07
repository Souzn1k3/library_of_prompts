import { MissionsClient } from "@/components/MissionsClient";
import type { MissionsLoadError } from "@/components/missions/useMissionsData";
import { ApiRequestError, fetchMissions } from "@/lib/api";
import { getTranslation } from "@/lib/i18n";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

export default async function MissionsPage() {
  const language = await getServerLanguage();
  const accessToken = await getServerAccessToken();
  let initialData = null;
  let initialError: MissionsLoadError = null;

  if (!accessToken) {
    initialError = "signed_out";
  } else {
    try {
      initialData = await fetchMissions(accessToken, language);
    } catch (error) {
      if (error instanceof ApiRequestError && error.status === 401) {
        initialError = "signed_out";
      } else {
        initialError =
          error instanceof ApiRequestError ? error.message : getTranslation(language, "missions.loadFailed");
      }
    }
  }

  return (
    <div className="pv-page">
      <MissionsClient initialData={initialData} initialError={initialError} />
    </div>
  );
}
