import Link from "next/link";

import { HomeWorkbenchContinuityBlocks } from "./HomeWorkbenchContinuityBlocks";

import type { ScenarioDefinition, ScenarioResultDepth } from "@/features/scenarios/domain/scenario";
import type { TranslationKey } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

type UnfinishedItem = {
  slug: string;
  task: string;
  updatedAt: string;
};

type HomeWorkbenchResultPanelProps = {
  t: (key: TranslationKey, params?: Record<string, string | number | null | undefined>) => string;
  selectedScenario: ScenarioDefinition | null;
  selectedPrompt: PromptListItem | null;
  liveResult: string;
  taskInput: string;
  onTaskInputChange: (value: string) => void;
  onTaskInputBlur: (value: string) => void;
  hasCurrentUnfinished: boolean;
  outputDepth: ScenarioResultDepth;
  onOutputDepthChange: (depth: ScenarioResultDepth) => void;
  onRunNow: () => void;
  runPending: boolean;
  onPurchaseBoost: () => void;
  boostPending: boolean;
  openScenarioHref: string;
  onCopy: () => void;
  onToggleSave: () => void;
  onShare: () => void;
  copyState: "idle" | "pending" | "copied" | "error";
  shareState: "idle" | "copied" | "error";
  isSaved: boolean;
  engagementMessage: string | null;
  runGuardMessage: string | null;
  lastRunAt: Date | null;
  demoStatus: {
    isPro: boolean;
    remainingRuns: number | null;
    capReached: boolean;
    bonusRunsRemaining: number | null;
  };
  unfinished: UnfinishedItem[];
  recentSlugs: string[];
  promptBySlug: Map<string, PromptListItem>;
  onResumeUnfinished: (slug: string, task: string) => void;
  onSelectRecent: (slug: string) => void;
  onMarkDone: () => void;
};

export function HomeWorkbenchResultPanel({
  t,
  selectedScenario,
  selectedPrompt,
  liveResult,
  taskInput,
  onTaskInputChange,
  onTaskInputBlur,
  hasCurrentUnfinished,
  outputDepth,
  onOutputDepthChange,
  onRunNow,
  runPending,
  onPurchaseBoost,
  boostPending,
  openScenarioHref,
  onCopy,
  onToggleSave,
  onShare,
  copyState,
  shareState,
  isSaved,
  engagementMessage,
  runGuardMessage,
  lastRunAt,
  demoStatus,
  unfinished,
  recentSlugs,
  promptBySlug,
  onResumeUnfinished,
  onSelectRecent,
  onMarkDone,
}: HomeWorkbenchResultPanelProps) {
  if (!selectedScenario) {
    return null;
  }

  const guardMessage =
    runGuardMessage?.startsWith("bonus_runs_added:")
      ? t("home.entryBoostAdded", { count: Number(runGuardMessage.split(":")[1] ?? "0") })
      : runGuardMessage === "boost_purchase_failed"
        ? t("home.entryBoostFailed")
      : runGuardMessage === "pro_unlimited_runs"
        ? t("home.entryDemoRunsUnlimited")
      :
    runGuardMessage === "free_demo_cap_reached"
      ? t("home.entryDemoCapReached")
      : runGuardMessage === "guest_ip_prompt_daily_cap_reached"
        ? t("home.entryDemoIpCapReached")
        : runGuardMessage === "guest_fingerprint_prompt_daily_cap_reached"
          ? t("home.entryDemoFingerprintCapReached")
          : runGuardMessage === "guest_ip_rotation_detected"
            ? t("home.entryDemoRotationCapReached")
        : runGuardMessage === "run_unavailable"
          ? t("home.entryRunUnavailable")
          : runGuardMessage;

  return (
    <aside className="pv-card p-5 sm:p-6">
      <div className="space-y-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
            {t("home.entryLiveStageKicker")}
          </p>
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{selectedScenario.title}</h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">{t("home.entryLiveStageSubtitle")}</p>
          {engagementMessage ? <p className="mt-2 text-xs font-semibold text-emerald-700">{engagementMessage}</p> : null}
          {guardMessage ? <p className="mt-1 text-xs font-semibold text-amber-700">{guardMessage}</p> : null}
          {lastRunAt ? (
            <p className="mt-1 text-xs text-zinc-500">{t("home.entryLastRun", { time: lastRunAt.toLocaleTimeString() })}</p>
          ) : null}
        </div>

        <div className="space-y-2">
          <label className="pv-label" htmlFor="home-task-input">
            {t("home.entryIntentLabel")}
          </label>
          <textarea
            id="home-task-input"
            value={taskInput}
            onChange={(event) => onTaskInputChange(event.target.value)}
            onBlur={(event) => onTaskInputBlur(event.target.value)}
            className="pv-textarea min-h-[98px]"
            placeholder={t("home.entryIntentPlaceholder")}
          />
          {hasCurrentUnfinished ? (
            <div className="rounded-[0.85rem] border border-zinc-200 bg-zinc-50 px-3 py-2 text-xs text-zinc-600">
              {t("home.entryUnfinishedHint")}
            </div>
          ) : null}
        </div>

        <div className="space-y-2">
          <p className="pv-label">{t("home.entryOutputDepthLabel")}</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => onOutputDepthChange("detailed")}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                outputDepth === "detailed"
                  ? "border-zinc-900 bg-zinc-900 text-white"
                  : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
              }`}
            >
              {t("home.entryOutputDepthDetailed")}
            </button>
            <button
              type="button"
              onClick={() => onOutputDepthChange("concise")}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                outputDepth === "concise"
                  ? "border-zinc-900 bg-zinc-900 text-white"
                  : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
              }`}
            >
              {t("home.entryOutputDepthConcise")}
            </button>
            <button
              type="button"
              onClick={onRunNow}
              className="rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-600 transition hover:border-zinc-300 hover:text-zinc-900"
              disabled={runPending}
            >
              {t("home.entryRefreshResult")}
            </button>
          </div>
        </div>

        <pre className="max-h-[17.2rem] overflow-auto rounded-[0.95rem] border border-zinc-200 bg-zinc-50 p-3 text-xs leading-relaxed text-zinc-700 whitespace-pre-wrap">
          {liveResult}
        </pre>

        <div className="space-y-2 rounded-[1rem] border border-zinc-200 bg-zinc-50/70 p-3">
          <p className="text-sm font-semibold text-zinc-900">{t("home.entryProGateTitle")}</p>
          <p className="text-sm leading-relaxed text-zinc-600">{t("home.entryProGateBody")}</p>
          {demoStatus.isPro ? (
            <p className="text-xs text-emerald-700">{t("home.entryDemoRunsUnlimited")}</p>
          ) : (
            <p className="text-xs text-zinc-500">
              {t("home.entryDemoRunsLeft", { count: demoStatus.remainingRuns ?? 0 })}
            </p>
          )}
          {!demoStatus.isPro && (demoStatus.bonusRunsRemaining ?? 0) > 0 ? (
            <p className="text-xs text-emerald-700">
              {t("home.entryBonusRunsRemaining", { count: demoStatus.bonusRunsRemaining ?? 0 })}
            </p>
          ) : null}
          {demoStatus.capReached ? <p className="text-xs text-amber-700">{t("home.entryDemoCapReached")}</p> : null}
          {!demoStatus.isPro ? (
            <button
              type="button"
              onClick={onPurchaseBoost}
              disabled={boostPending}
              className="pv-button-secondary !w-auto disabled:opacity-60"
            >
              {boostPending ? t("home.entryBoostPending") : t("home.entryBoostAction")}
            </button>
          ) : null}
        </div>

        <div className="flex flex-wrap gap-2">
          <button type="button" onClick={onRunNow} className="pv-button-primary" disabled={runPending || demoStatus.capReached}>
            {runPending ? t("home.entryRunPending") : t("home.entryRunNow")}
          </button>
          <Link href={openScenarioHref} className="pv-button-secondary !w-auto">
            {t("home.entryPrimaryAction")}
          </Link>
          <button
            type="button"
            onClick={onCopy}
            disabled={copyState === "pending"}
            className="pv-button-secondary !w-auto disabled:opacity-60"
          >
            {copyState === "copied" ? t("home.entryCopySuccess") : copyState === "pending" ? t("copy.copying") : t("home.entryCopyAction")}
          </button>
          <button type="button" onClick={onToggleSave} className="pv-button-secondary !w-auto">
            {isSaved ? t("home.entrySavedAction") : t("home.entrySaveAction")}
          </button>
          <button type="button" onClick={onShare} className="pv-button-secondary !w-auto">
            {shareState === "copied" ? t("home.entryShareCopied") : t("home.entryShareAction")}
          </button>
        </div>

        {copyState === "error" ? <p className="text-sm text-red-700">{t("home.entryCopyError")}</p> : null}
        {shareState === "error" ? <p className="text-sm text-red-700">{t("home.entryShareError")}</p> : null}

        <HomeWorkbenchContinuityBlocks
          t={t}
          unfinished={unfinished}
          recentSlugs={recentSlugs}
          promptBySlug={promptBySlug}
          onResume={onResumeUnfinished}
          onSelectRecent={onSelectRecent}
        />

        {hasCurrentUnfinished && selectedPrompt ? (
          <button type="button" onClick={onMarkDone} className="text-xs font-semibold text-zinc-500">
            {t("home.entryMarkDone")}
          </button>
        ) : null}
      </div>
    </aside>
  );
}
