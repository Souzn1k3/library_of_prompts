import { fetchLearningMyModules } from "@/lib/api";
import type { Language } from "@/lib/i18n";
import type { LearningMyModules } from "@/lib/types";

export type MyLearningPageData =
  | { mode: "guest" }
  | {
      mode: "member";
      modules: LearningMyModules;
    };

export async function loadMyLearningPageData({
  accessToken,
  language,
}: {
  accessToken: string | null | undefined;
  language: Language;
}): Promise<MyLearningPageData> {
  if (!accessToken) {
    return { mode: "guest" };
  }

  return {
    mode: "member",
    modules: await fetchLearningMyModules(accessToken, language),
  };
}
