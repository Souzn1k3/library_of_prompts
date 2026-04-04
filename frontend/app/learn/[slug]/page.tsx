import { redirect } from "next/navigation";

import { locateLearningLessonBySlug } from "@/lib/api";
import { appRoute, LEARNING_FOUNDATIONS_COURSE_SLUG } from "@/lib/constants/routes";
import { getServerAccessToken } from "@/lib/server-auth";
import { getServerLanguage } from "@/lib/server-i18n";

type Props = { params: Promise<{ slug: string }> };

export default async function LegacyLessonCompatibilityPage(props: Props) {
  const { slug } = await props.params;
  const accessToken = await getServerAccessToken();
  const language = await getServerLanguage();

  try {
    const locate = await locateLearningLessonBySlug(slug, accessToken, language);
    if (locate?.href) {
      redirect(locate.href);
    }
  } catch {
    // If the legacy lookup fails, route users to the foundations course instead.
  }

  redirect(appRoute.learnCourse(LEARNING_FOUNDATIONS_COURSE_SLUG));
}
