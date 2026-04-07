"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import { fetchMissions } from "@/lib/client-api";
import type { MissionListRead } from "@/lib/types";

export type MissionsLoadError = "signed_out" | string | null;

type UseMissionsDataArgs = {
  language: string;
  loadFailedMessage: string;
  initialData?: MissionListRead | null;
  initialError?: MissionsLoadError;
};

type UseMissionsDataResult = {
  data: MissionListRead | null;
  error: MissionsLoadError;
  loading: boolean;
  reload: () => void;
};

export function useMissionsData({
  language,
  loadFailedMessage,
  initialData = null,
  initialError = null,
}: UseMissionsDataArgs): UseMissionsDataResult {
  const hasInitialState = initialData !== null || initialError !== null;
  const skipInitialFetchRef = useRef(hasInitialState);
  const [data, setData] = useState<MissionListRead | null>(initialData);
  const [error, setError] = useState<MissionsLoadError>(initialError);
  const [loading, setLoading] = useState(!hasInitialState);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  useEffect(() => {
    if (skipInitialFetchRef.current) {
      skipInitialFetchRef.current = false;
      return;
    }

    let cancelled = false;
    setLoading(true);

    fetchMissions()
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setData(payload);
        setError(null);
      })
      .catch((requestError) => {
        if (cancelled) {
          return;
        }
        setData(null);
        if (requestError instanceof ApiRequestError && requestError.status === 401) {
          setError("signed_out");
          return;
        }
        setError(requestError instanceof Error ? requestError.message : loadFailedMessage);
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [language, loadFailedMessage, reloadToken]);

  return {
    data,
    error,
    loading,
    reload,
  };
}
