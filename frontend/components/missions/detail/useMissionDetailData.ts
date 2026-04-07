"use client";

import { useEffect, useRef, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import { fetchMissionBySlug } from "@/lib/client-api";
import type { Language } from "@/lib/i18n";
import type { MissionRead } from "@/lib/types";

type UseMissionDetailDataArgs = {
  slug: string;
  language: Language;
  loadFailedMessage: string;
  initialMission?: MissionRead | null;
  initialError?: string | null;
  initialSignedOut?: boolean;
};

export function useMissionDetailData({
  slug,
  language,
  loadFailedMessage,
  initialMission = null,
  initialError = null,
  initialSignedOut = false,
}: UseMissionDetailDataArgs) {
  const hasInitialState = Boolean(initialMission) || Boolean(initialError) || initialSignedOut;
  const skipInitialFetchRef = useRef(hasInitialState);
  const [mission, setMission] = useState<MissionRead | null>(initialMission);
  const [error, setError] = useState<string | null>(initialError);
  const [isSignedOut, setIsSignedOut] = useState(initialSignedOut);
  const [loading, setLoading] = useState(!hasInitialState);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (skipInitialFetchRef.current) {
      skipInitialFetchRef.current = false;
      return;
    }

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
