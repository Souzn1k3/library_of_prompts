"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

import type { AuthStatus } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { ApiRequestError } from "@/lib/api";
import {
  fetchBillingStatus,
  fetchCurrentMission,
  fetchLearningCourse,
  fetchLearningMyModules,
  fetchMySubmissions,
  fetchOnboardingProfile,
  fetchOnboardingStarterPack,
  fetchPromptRecommendations,
  fetchSavedPrompts,
  fetchWallet,
} from "@/lib/client-api";
import type {
  AuthorSubmission,
  BillingStatus,
  LearningCourseDetail,
  LearningMyModules,
  MissionCurrentRead,
  OnboardingProfile,
  OnboardingStarterPack,
  PromptListItem,
  WalletRead,
} from "@/lib/types";

export function useDashboardData(status: AuthStatus) {
  const { t } = useI18n();
  const searchParams = useSearchParams();
  const billingQueryState = searchParams.get("billing");
  const [items, setItems] = useState<PromptListItem[] | null>(null);
  const [recommended, setRecommended] = useState<PromptListItem[]>([]);
  const [submissions, setSubmissions] = useState<AuthorSubmission[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [wallet, setWallet] = useState<WalletRead | null>(null);
  const [missionCurrent, setMissionCurrent] = useState<MissionCurrentRead | null>(null);
  const [onboardingProfile, setOnboardingProfile] = useState<OnboardingProfile | null>(null);
  const [starterPack, setStarterPack] = useState<OnboardingStarterPack | null>(null);
  const [learningMy, setLearningMy] = useState<LearningMyModules | null>(null);
  const [learningCourse, setLearningCourse] = useState<LearningCourseDetail | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    if (status !== "authenticated") {
      setItems(null);
      setRecommended([]);
      setSubmissions([]);
      setError(null);
      setBilling(null);
      setWallet(null);
      setMissionCurrent(null);
      setOnboardingProfile(null);
      setStarterPack(null);
      setLearningMy(null);
      setLearningCourse(null);
      return;
    }

    let cancelled = false;

    async function loadDashboard() {
      const [
        savedResult,
        recommendedResult,
        billingResult,
        walletResult,
        submissionsResult,
        onboardingResult,
        starterResult,
        missionResult,
        learningMyResult,
      ] = await Promise.allSettled([
        fetchSavedPrompts(),
        fetchPromptRecommendations({ context: "dashboard", limit: 4 }),
        fetchBillingStatus(),
        fetchWallet(),
        fetchMySubmissions(),
        fetchOnboardingProfile(),
        fetchOnboardingStarterPack(),
        fetchCurrentMission(),
        fetchLearningMyModules(),
      ]);

      if (cancelled) return;

      const requiredFailures = [savedResult, billingResult, submissionsResult].filter(
        (result): result is PromiseRejectedResult => result.status === "rejected",
      );

      if (requiredFailures.length > 0) {
        const reason = requiredFailures[0].reason;
        if (reason instanceof ApiRequestError && reason.status === 401) {
          setItems(null);
          setRecommended([]);
          return;
        }
        setError(reason instanceof ApiRequestError ? reason.message : t("dashboard.loadError"));
        setItems([]);
        setRecommended([]);
        setBilling(null);
        setWallet(null);
        setSubmissions([]);
        return;
      }

      if (
        savedResult.status !== "fulfilled" ||
        billingResult.status !== "fulfilled" ||
        submissionsResult.status !== "fulfilled"
      ) {
        setError(t("dashboard.loadError"));
        setItems([]);
        setRecommended([]);
        setBilling(null);
        setWallet(null);
        setSubmissions([]);
        return;
      }

      setItems(savedResult.value);
      setRecommended(recommendedResult.status === "fulfilled" ? recommendedResult.value.items : []);
      setBilling(billingResult.value);
      setWallet(walletResult.status === "fulfilled" ? walletResult.value : null);
      setSubmissions(submissionsResult.value);
      setError(null);
      setOnboardingProfile(onboardingResult.status === "fulfilled" ? onboardingResult.value : null);
      setStarterPack(starterResult.status === "fulfilled" ? starterResult.value : null);
      setMissionCurrent(missionResult.status === "fulfilled" ? missionResult.value : null);

      const learningSummary = learningMyResult.status === "fulfilled" ? learningMyResult.value : null;
      setLearningMy(learningSummary);
      setLearningCourse(null);

      const learningCourseSlug =
        learningSummary?.active_courses[0]?.slug ?? learningSummary?.completed_courses[0]?.slug ?? null;

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
  }, [reloadToken, status, t]);

  useEffect(() => {
    if (status !== "authenticated") return;
    if (billingQueryState !== "success") return;
    let attempt = 0;
    const maxAttempts = 12;
    const interval = window.setInterval(() => {
      attempt += 1;
      fetchBillingStatus()
        .then((nextStatus) => {
          setBilling(nextStatus);
          const ready = nextStatus.status === "active" || nextStatus.status === "trialing";
          if (ready || attempt >= maxAttempts) {
            window.clearInterval(interval);
          }
        })
        .catch(() => {
          if (attempt >= maxAttempts) {
            window.clearInterval(interval);
          }
        });
    }, 2500);
    return () => window.clearInterval(interval);
  }, [billingQueryState, status]);

  return {
    items,
    recommended,
    submissions,
    error,
    billing,
    wallet,
    missionCurrent,
    onboardingProfile,
    starterPack,
    learningMy,
    learningCourse,
    submitted: searchParams.get("submitted") === "1",
    autoApproved: searchParams.get("autoApproved") === "1",
    reload: () => setReloadToken((value) => value + 1),
  };
}
