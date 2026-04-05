"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import {
  loadDashboardSnapshot,
  selectLearningCourseSlug,
} from "@/components/dashboard/dashboardDataLoader";
import {
  createEmptyDashboardState,
  dashboardStateFromSnapshot,
} from "@/components/dashboard/dashboardState";
import { useBillingActivationPolling } from "@/components/dashboard/useBillingActivationPolling";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { fetchLearningCourse } from "@/lib/client-api";
import type { BillingStatus, LearningCourseDetail } from "@/lib/types";

export function useDashboardData(status: AuthStatus) {
  const { t } = useI18n();
  const searchParams = useSearchParams();
  const billingQueryState = searchParams.get("billing");

  const [state, setState] = useState(createEmptyDashboardState);
  const [reloadToken, setReloadToken] = useState(0);

  const resetDashboardState = useCallback(() => {
    setState(createEmptyDashboardState());
  }, []);

  const applySnapshot = useCallback((snapshot: Awaited<ReturnType<typeof loadDashboardSnapshot>>) => {
    setState(dashboardStateFromSnapshot(snapshot));
  }, []);

  const setLearningCourse = useCallback((course: LearningCourseDetail | null) => {
    setState((prev) => ({ ...prev, learningCourse: course }));
  }, []);

  const updateBilling = useCallback((billing: BillingStatus) => {
    setState((prev) => ({ ...prev, billing }));
  }, []);

  useEffect(() => {
    if (status !== "authenticated") {
      resetDashboardState();
      return;
    }

    let cancelled = false;

    async function loadDashboard() {
      const snapshot = await loadDashboardSnapshot(t);
      if (cancelled) {
        return;
      }
      if (snapshot.unauthorized) {
        resetDashboardState();
        return;
      }
      applySnapshot(snapshot);

      const learningCourseSlug = selectLearningCourseSlug(snapshot.learningMy);

      if (!learningCourseSlug) {
        return;
      }

      void fetchLearningCourse(learningCourseSlug)
        .then((course) => {
          if (cancelled) return;
          setLearningCourse(course);
        })
        .catch(() => {
          if (cancelled) return;
          setLearningCourse(null);
        });
    }

    void loadDashboard();
    return () => {
      cancelled = true;
    };
  }, [applySnapshot, reloadToken, resetDashboardState, setLearningCourse, status, t]);

  useBillingActivationPolling({
    status,
    billingQueryState,
    onBillingUpdate: updateBilling,
  });

  return {
    ...state,
    submitted: searchParams.get("submitted") === "1",
    autoApproved: searchParams.get("autoApproved") === "1",
    reload: () => setReloadToken((value) => value + 1),
  };
}
