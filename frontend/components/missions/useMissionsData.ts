"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import { fetchMissions } from "@/lib/client-api";
import type { MissionListRead } from "@/lib/types";

export type MissionsLoadError = "signed_out" | string | null;

type UseMissionsDataArgs = {
  language: string;
  loadFailedMessage: string;
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
}: UseMissionsDataArgs): UseMissionsDataResult {
  const [data, setData] = useState<MissionListRead | null>(null);
  const [error, setError] = useState<MissionsLoadError>(null);
  const [loading, setLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  useEffect(() => {
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
