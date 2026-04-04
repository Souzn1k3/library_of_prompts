"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { formatNumber } from "@/lib/formatters";
import { languageToIntlLocale } from "@/lib/i18n";

type DailyLadderStep = {
  day: number;
  reward: number;
  isActive: boolean;
  isComplete: boolean;
  isBigReward: boolean;
};

type StreakMilestone = {
  streak: number;
  reward: number;
};

type ProgressAndRewardsProps = {
  ladder: DailyLadderStep[];
  streakMilestones: ReadonlyArray<StreakMilestone>;
  currentStreak: number;
  nextMilestone: StreakMilestone | null;
  rankLevel: number;
  rankPoints: number;
  rankNextThreshold: number;
  ownedValueGenerated: number;
};

export function ProgressAndRewards({
  ladder,
  streakMilestones,
  currentStreak,
  nextMilestone,
  rankLevel,
  rankPoints,
  rankNextThreshold,
  ownedValueGenerated,
}: ProgressAndRewardsProps) {
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);
  const compactLadder = ladder.slice(0, 6);
  const extendedStep = ladder[6] ?? null;
  const rankPercent = Math.max(
    4,
    Math.min(100, Math.round((rankPoints / Math.max(1, rankNextThreshold)) * 100)),
  );

  return (
    <section className="pv-panel h-full px-5 py-5">
      <p className="pv-kicker">{progressAndRewardsTitle(language)}</p>
      <div className="mt-4 space-y-4">
        <div className="rounded-xl border border-[rgba(15,23,42,0.08)] bg-white/80 p-3">
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-zinc-500">
            {t("wallet.dailyLadder")}
          </p>
          <div className="mt-3 grid grid-cols-3 gap-2" data-testid="wallet-daily-ladder">
            {compactLadder.map((step) => (
              <div
                key={step.day}
                className={`rounded-lg border px-2 py-2 text-center ${
                  step.isActive
                    ? "border-[var(--pv-brand)] bg-[rgba(37,92,255,0.1)]"
                    : step.isComplete
                      ? "border-emerald-200 bg-emerald-50/70"
                      : "border-zinc-200 bg-zinc-50/80"
                }`}
                data-testid={`wallet-daily-ladder-step-${step.day}`}
              >
                <p className="text-[0.62rem] font-semibold uppercase tracking-[0.12em] text-zinc-500">
                  {t("wallet.dayLabel", { day: step.day })}
                </p>
                <p className="mt-1 text-sm font-semibold text-zinc-950">+{step.reward}</p>
              </div>
            ))}
          </div>
          {extendedStep ? (
            <p className="mt-2 text-xs text-zinc-500">
              {t("wallet.dayLabel", { day: extendedStep.day })}: +{extendedStep.reward}
            </p>
          ) : null}
        </div>

        <div className="rounded-xl border border-[rgba(15,23,42,0.08)] bg-white/80 p-3">
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-zinc-500">
            {t("wallet.streakMilestones")}
          </p>
          <div className="mt-2 space-y-2">
            {streakMilestones.slice(0, 4).map((milestone) => {
              const reached = currentStreak >= milestone.streak;
              return (
                <div key={milestone.streak} className="flex items-center justify-between gap-2 rounded-lg bg-zinc-50/80 px-2.5 py-2">
                  <div>
                    <p className="text-xs font-semibold text-zinc-900">
                      {t("wallet.milestoneLabel", { count: milestone.streak })}
                    </p>
                    <p className="text-[0.68rem] text-zinc-600">{t("wallet.milestoneReward", { amount: milestone.reward })}</p>
                  </div>
                  <span className={reached ? "pv-badge-success" : "pv-badge"}>
                    {reached ? t("wallet.reached") : t("wallet.upcoming")}
                  </span>
                </div>
              );
            })}
          </div>
          {nextMilestone ? (
            <p className="mt-2 text-xs text-zinc-500">
              {t("wallet.nextMilestone", { count: nextMilestone.streak, amount: nextMilestone.reward })}
            </p>
          ) : null}
        </div>

        <div className="rounded-xl border border-[rgba(15,23,42,0.08)] bg-white/80 p-3">
          <div className="flex items-center justify-between gap-2">
            <p className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-zinc-500">
              {t("wallet.vaultRank")}
            </p>
            <p className="text-xs font-medium text-zinc-600">
              {t("wallet.rankLevelProgress", {
                level: formatNumber(rankLevel, locale),
                points: formatNumber(rankPoints, locale),
                threshold: formatNumber(rankNextThreshold, locale),
              })}
            </p>
          </div>
          <div className="mt-2 pv-progress">
            <div className="pv-progress-fill" style={{ width: `${rankPercent}%` }} />
          </div>
          <p className="mt-2 text-xs text-zinc-500">
            {t("wallet.ownedValueGenerated", { amount: formatNumber(ownedValueGenerated, locale) })}
          </p>
        </div>
      </div>
    </section>
  );
}

function progressAndRewardsTitle(language: string): string {
  if (language === "ru") {
    return "Прогресс и награды";
  }
  if (language === "tt") {
    return "Прогресс һәм бүләкләр";
  }
  return "Progress and rewards";
}
