"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { getApiBaseUrl } from "@/lib/api";
import { API_ENDPOINTS } from "@/lib/constants/api";
import { APP_ROUTES } from "@/lib/constants/routes";
import { getClientLanguage } from "@/lib/i18n";

type LearningStartTarget = {
  target?: string | null;
};

async function resolveStartTarget(): Promise<string> {
  const language = getClientLanguage();
  const headers: HeadersInit = {
    Accept: "application/json",
    "Accept-Language": language,
  };
  const startTargetUrl = `${getApiBaseUrl()}${API_ENDPOINTS.learningStartTarget}`;

  let response = await fetch(startTargetUrl, {
    method: "GET",
    headers,
    credentials: "include",
    cache: "no-store",
  });

  if (response.status === 401) {
    await fetch(`${getApiBaseUrl()}${API_ENDPOINTS.auth.refresh}`, {
      method: "POST",
      headers,
      credentials: "include",
      cache: "no-store",
    });
    response = await fetch(startTargetUrl, {
      method: "GET",
      headers,
      credentials: "include",
      cache: "no-store",
    });
  }

  if (!response.ok) {
    return APP_ROUTES.learn;
  }

  const payload = (await response.json()) as LearningStartTarget;
  return payload.target || APP_ROUTES.learn;
}

export default function LearnStartPage() {
  const router = useRouter();
  const { t } = useI18n();

  useEffect(() => {
    let mounted = true;
    void (async () => {
      const target = await resolveStartTarget();
      if (mounted) {
        router.replace(target);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [router]);

  return (
    <div className="pv-page-sm">
      <div className="pv-panel px-6 py-6 sm:px-7">
        <p className="text-sm text-zinc-600">{t("learn.preparingPath")}</p>
      </div>
    </div>
  );
}
