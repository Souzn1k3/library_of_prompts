"use client";

import { useEffect, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import { fetchMissionBySlug } from "@/lib/client-api";
import type { Language } from "@/lib/i18n";
import type { MissionRead } from "@/lib/types";

type UseMissionDetailDataArgs = {
  slug: string;
  language: Language;
  loadFailedMessage: string;
};

export function useMissionDetailData({ slug, language, loadFailedMessage }: UseMissionDetailDataArgs) {
  const [mission, setMission] = useState<MissionRead | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSignedOut, setIsSignedOut] = useState(false);
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let isCancelled = false;
    setLoading(true);
    setIsSignedOut(false);

    fetchMissionBySlug(slug)
      .then((row) => {
        if (isCancelled) {
          return;
        }
        setMission(row);
        setError(null);
      })
      .catch((errorResponse: unknown) => {
        if (isCancelled) {
          return;
        }
        setMission(null);
        if (errorResponse instanceof ApiRequestError && errorResponse.status === 401) {
          setIsSignedOut(true);
          setError(null);
          return;
        }
        setError(errorResponse instanceof Error ? errorResponse.message : loadFailedMessage);
      })
      .finally(() => {
        if (isCancelled) {
          return;
        }
        setLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, [language, loadFailedMessage, reloadToken, slug]);

  return {
    mission,
    error,
    isSignedOut,
    loading,
    retry: () => setReloadToken((value) => value + 1),
  };
}
