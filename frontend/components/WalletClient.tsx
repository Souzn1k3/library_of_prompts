"use client";

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import { PageIntro } from "@/components/navigation/PageIntro";
import { EconomyActionBanner } from "@/components/ui/EconomyActionBanner";
import { LmnAmount } from "@/components/ui/LmnAmount";
import { LmnBalanceCard } from "@/components/ui/LmnBalanceCard";
import { useLmnBalanceFeedback } from "@/components/ui/useLmnBalanceFeedback";
import { ApiRequestError } from "@/lib/api";
import { APP_ROUTES } from "@/lib/constants/routes";
import {
  buildClientEconomyAction,
  buildDailyLadder,
  nextMilestone,
  pickBestStoreItem,
  resolveStreakMilestones,
} from "@/lib/economy";
import { fetchStoreItems, fetchWallet, walletCheckIn } from "@/lib/client-api";
import { formatDateTime, formatMultiplier, formatNumber, humanizeSnakeCase } from "@/lib/formatters";
import { languageToIntlLocale, type TranslationKey } from "@/lib/i18n";
import type { CurrencyTransaction, EconomyAction, StoreItem, WalletBenefit, WalletPurchase, WalletRead } from "@/lib/types";

function formatAmount(amount: number): string {
  const sign = amount > 0 ? "+" : "";
  return `${sign}${amount}`;
}

function reasonLabel(reason: string, t: ReturnType<typeof useI18n>["t"]): string {
  const key = `wallet.transaction.reason.${reason}` as TranslationKey;
  const translated = t(key);
  return translated === key ? humanizeSnakeCase(reason) : translated;
}

function benefitLabel(
  benefit: WalletBenefit,
  t: ReturnType<typeof useI18n>["t"],
  locale: string,
) {
  if (benefit.kind === "subscription_discount" || benefit.kind === "starter") {
    const code = typeof benefit.metadata?.code === "string" ? benefit.metadata.code : null;
    const percent = benefit.metadata?.discount_percent;
    if (code) {
      if (typeof percent === "number") {
        return `${formatNumber(percent, locale)}% · ${code}`;
      }
      return code;
    }
    return typeof benefit.metadata?.item_title === "string"
      ? String(benefit.metadata.item_title)
      : t("store.kind.starter");
  }
  if (benefit.kind === "premium_access") {
    return t("store.kind.premium_pass");
  }
  if (benefit.kind === "premium_prompt_unlock") {
    return typeof benefit.metadata?.prompt_title === "string"
      ? String(benefit.metadata.prompt_title)
      : t("store.kind.premium_prompt_unlock");
  }
  if (benefit.kind === "prompt_bundle") {
    return typeof benefit.metadata?.item_title === "string"
      ? String(benefit.metadata.item_title)
      : t("store.kind.prompt_bundle");
  }
  return humanizeSnakeCase(benefit.kind);
}

function benefitKindLabel(kind: string, t: ReturnType<typeof useI18n>["t"]): string {
  if (kind === "premium_access") {
    return t("store.kind.premium_pass");
  }
  if (kind === "boost") {
    return t("store.kind.boost");
  }
  const key = `store.kind.${kind}` as TranslationKey;
  const translated = t(key);
  return translated === key ? humanizeSnakeCase(kind) : translated;
}

function localizedGoalCopy(
  goal: WalletRead["goals"][number],
  t: ReturnType<typeof useI18n>["t"],
): { layer: string; title: string; description: string } {
  const layerKey = `wallet.goal.layer.${goal.layer}` as TranslationKey;
  const translatedLayer = t(layerKey);
  const layer = translatedLayer === layerKey ? goal.layer : translatedLayer;

  const slugOrLevel = goal.key.includes(":") ? goal.key.split(":")[1] : null;
  const titleSuffix = goal.title.includes(":") ? goal.title.split(":").slice(1).join(":").trim() : "";
  const fallbackTitle = titleSuffix || slugOrLevel?.replaceAll("-", " ") || goal.title;

  if (goal.key.startsWith("next-item:")) {
    return {
      layer,
      title: t("wallet.goal.nextUnlockTitle", { title: fallbackTitle }),
      description: t("wallet.goal.nextUnlockDescription"),
    };
  }
  if (goal.key.startsWith("buy-now:")) {
    return {
      layer,
      title: t("wallet.goal.buyNowTitle", { title: fallbackTitle }),
      description: t("wallet.goal.buyNowDescription"),
    };
  }
  if (goal.key === "next-earn") {
    return {
      layer,
      title: t("wallet.goal.nextEarnTitle"),
      description: t("wallet.goal.nextEarnDescription"),
    };
  }
  if (goal.key.startsWith("inactive-comeback:")) {
    return {
      layer,
      title: t("wallet.goal.comebackTitle", { count: goal.target }),
      description: t("wallet.goal.comebackDescription"),
    };
  }
  if (goal.key.startsWith("hoarder-convert:")) {
    return {
      layer,
      title: t("wallet.goal.hoarderTitle", { count: goal.target }),
      description: t("wallet.goal.hoarderDescription"),
    };
  }
  if (goal.key.startsWith("spender-maintain:")) {
    return {
      layer,
      title: t("wallet.goal.spenderTitle", { count: goal.target }),
      description: t("wallet.goal.spenderDescription"),
    };
  }
  if (goal.key.startsWith("habit-window:")) {
    return {
      layer,
      title: t("wallet.goal.habitTitle", { count: goal.target }),
      description: t("wallet.goal.habitDescription"),
    };
  }
  if (goal.key.startsWith("rank:")) {
    const level = slugOrLevel ?? String(goal.target);
    return {
      layer,
      title: t("wallet.goal.rankTitle", { level }),
      description: t("wallet.goal.rankDescription"),
    };
  }
  return {
    layer,
    title: goal.title || t("wallet.goal.unknown"),
    description: goal.description,
  };
}

export function WalletClient() {
  const { status } = useAuth();
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);
  const [wallet, setWallet] = useState<WalletRead | null>(null);
  const [items, setItems] = useState<StoreItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkinPending, setCheckinPending] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [checkinFeedback, setCheckinFeedback] = useState<EconomyAction | null>(null);
  const [activityPage, setActivityPage] = useState(1);
  const { change: balanceChange, delta: balanceDelta } = useLmnBalanceFeedback(wallet?.balance);

  useEffect(() => {
    if (status !== "authenticated") {
      setLoading(status === "loading");
      return;
    }
    let cancelled = false;
    setLoading(true);
    Promise.all([fetchWallet(), fetchStoreItems()])
      .then(([walletData, storeItems]) => {
        if (cancelled) return;
        setWallet(walletData);
        setItems(storeItems);
        setError(null);
      })
      .catch((e) => {
        if (cancelled) return;
        setWallet(null);
        setItems([]);
        setError(e instanceof ApiRequestError ? e.message : t("wallet.checkInError"));
      })
      .finally(() => {
        if (cancelled) return;
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [status, reloadToken, t]);

  useEffect(() => {
    setActivityPage(1);
  }, [wallet?.recent.length]);

  async function handleCheckIn() {
    setCheckinPending(true);
    try {
      const previousBalance = wallet?.balance ?? 0;
      const [walletData, storeItems] = await Promise.all([walletCheckIn(), fetchStoreItems()]);
      setWallet(walletData);
      setItems(storeItems);
      setError(null);
      setCheckinFeedback(
        buildClientEconomyAction({
          balanceDelta: walletData.balance - previousBalance,
          items: storeItems,
          previousBalance,
        }),
      );
    } catch (e) {
      setError(e instanceof ApiRequestError ? e.message : t("wallet.checkInError"));
      setCheckinFeedback(null);
    } finally {
      setCheckinPending(false);
    }
  }

  if (status === "loading" || loading) {
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
            { label: t("nav.economy") },
            { label: t("nav.wallet") },
          ]}
          eyebrow={t("nav.wallet")}
          title={t("wallet.title")}
          description={t("wallet.subtitle")}
          hint={t("economy.loopBody")}
        />
        <p className="text-sm text-zinc-500">{t("missions.loading")}</p>
      </div>
    );
  }

  if (status === "unauthenticated") {
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
            { label: t("nav.economy") },
            { label: t("nav.wallet") },
          ]}
          eyebrow={t("nav.wallet")}
          title={t("wallet.title")}
          description={t("wallet.subtitle")}
          hint={t("wallet.guestHint")}
          actions={
            <>
              <Link href={APP_ROUTES.login} className="pv-button-primary">
                {t("nav.login")}
              </Link>
              <Link href={APP_ROUTES.signup} className="pv-button-secondary">
                {t("nav.signup")}
              </Link>
            </>
          }
        />
        <div className="pv-empty-state text-sm text-zinc-600">
          {t("wallet.signInPrefix")}{" "}
          <Link href={APP_ROUTES.login} className="font-medium text-zinc-900 underline">
            {t("wallet.signInLink")}
          </Link>{" "}
          {t("wallet.signInSuffix")}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageIntro
          breadcrumbs={[
            { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
            { label: t("nav.economy") },
            { label: t("nav.wallet") },
          ]}
          eyebrow={t("nav.wallet")}
          title={t("wallet.title")}
          description={t("wallet.subtitle")}
          hint={t("economy.loopBody")}
        />
        <div className="pv-alert pv-alert-warning space-y-3">
          <p>{error}</p>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setReloadToken((value) => value + 1)}
              className="pv-button-secondary !w-auto"
            >
              {t("wallet.refresh")}
            </button>
            <button type="button" onClick={handleCheckIn} className="pv-button-primary !w-auto">
              {t("wallet.checkinCta")}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!wallet) return null;

  const activityPageSize = 10;
  const totalActivityPages = Math.max(1, Math.ceil(wallet.recent.length / activityPageSize));
  const currentActivityPage = Math.min(activityPage, totalActivityPages);
  const activityStart = (currentActivityPage - 1) * activityPageSize;
  const pagedRecent = wallet.recent.slice(activityStart, activityStart + activityPageSize);
  const checkInMessage = wallet.check_in_available
    ? t("wallet.checkinReady")
    : `${t("wallet.checkinLocked")}${wallet.last_check_in_at ? ` · ${formatDateTime(wallet.last_check_in_at, locale)}` : ""}`;
  const bestItem = pickBestStoreItem(items);
  const readyToBuyCount = items.filter(
    (item) => !item.owned && item.is_affordable && (item.availability === null || item.availability > 0),
  ).length;
  const ladder = buildDailyLadder(wallet.current_streak, wallet);
  const streakMilestones = resolveStreakMilestones(wallet);
  const nextMilestoneEntry = nextMilestone(wallet.current_streak, wallet);

  return (
    <div className="space-y-6">
      <EconomyActionBanner summary={checkinFeedback} />

      <PageIntro
        breadcrumbs={[
          { label: t("nav.dashboard"), href: APP_ROUTES.dashboard },
          { label: t("nav.economy") },
          { label: t("nav.wallet") },
        ]}
        eyebrow={t("nav.wallet")}
        title={t("wallet.title")}
        description={t("wallet.subtitle")}
        hint={
          bestItem
            ? bestItem.is_affordable
              ? t("wallet.bestUseReady", { title: bestItem.title })
              : t("wallet.bestUseAlmost", { title: bestItem.title, count: bestItem.remaining_lumens })
            : checkInMessage
        }
        actions={
          <>
            <button
              type="button"
              onClick={handleCheckIn}
              disabled={checkinPending || !wallet.check_in_available}
              className="pv-button-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {checkinPending ? t("missions.loading") : t("wallet.checkinCta")}
            </button>
          </>
        }
        aside={
          <div className="grid gap-3 sm:grid-cols-3 xl:grid-cols-1">
            <div className="sm:col-span-3 xl:col-span-1">
              <LmnBalanceCard
                label={t("wallet.balance")}
                amount={wallet.balance}
                symbol={wallet.currency_symbol}
                caption={wallet.currency_name || wallet.currency_symbol}
                detail={wallet.check_in_available ? t("wallet.checkinReady") : t("wallet.checkinLocked")}
                delta={balanceDelta}
                change={balanceChange}
              />
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("wallet.currentStreak")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">{wallet.current_streak}</p>
            </div>
            <div className="pv-stat-card">
              <p className="pv-stat-label">{t("wallet.spendStreak")}</p>
              <p className="mt-3 text-2xl font-extrabold tracking-[-0.05em] text-zinc-950">
                {t("wallet.spendStreakValue", {
                  days: formatNumber(wallet.spend_streak_days, locale),
                  mult: formatMultiplier(wallet.spend_streak_mult, locale),
                })}
              </p>
            </div>
          </div>
        }
      />

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px] xl:items-start">
        <section className="pv-panel px-5 py-5">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("wallet.nextSpend")}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("wallet.nextSpend")}</h2>
              <p className="mt-2 text-sm text-zinc-600">{t("wallet.bestUse")}</p>
            </div>
            {bestItem ? (
              <LmnAmount amount={bestItem.price} symbol={wallet.currency_symbol} strong state="spent" />
            ) : (
              <LmnAmount amount={wallet.balance} symbol={wallet.currency_symbol} strong state="balance" />
            )}
          </div>

          {bestItem ? (
            <div className="mt-5 space-y-4">
              <div className="pv-card-muted p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-zinc-900">{bestItem.title}</p>
                    <p className="mt-1 text-sm text-zinc-600">
                      {bestItem.is_affordable
                        ? t("wallet.bestUseReady", { title: bestItem.title })
                        : t("wallet.bestUseAlmost", { title: bestItem.title, count: bestItem.remaining_lumens })}
                    </p>
                  </div>
                  {bestItem.is_affordable ? (
                    <span className="pv-badge-success">{t("store.availableNow")}</span>
                  ) : (
                    <span className="pv-badge-warning">{t("store.remaining", { count: bestItem.remaining_lumens })}</span>
                  )}
                </div>
                <div className="mt-4 pv-progress">
                  <div
                    className="pv-progress-fill"
                    style={{ width: `${Math.max(bestItem.progress_ratio > 0 ? 8 : 0, Math.round(bestItem.progress_ratio * 100))}%` }}
                  />
                </div>
              </div>

              <div className="flex flex-wrap gap-3">
                <Link href={bestItem.is_affordable ? APP_ROUTES.store : APP_ROUTES.missions} className="pv-button-primary">
                  {bestItem.is_affordable ? t("wallet.spendNowCta") : t("wallet.earnToUnlockCta")}
                </Link>
                <Link href={APP_ROUTES.store} className="pv-button-secondary">
                  {t("economy.openStore")}
                </Link>
              </div>
            </div>
          ) : (
            <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("store.empty")}</div>
          )}
        </section>

        <aside className="space-y-4">
          <section className="pv-panel px-5 py-5">
            <p className="pv-kicker">{t("wallet.dailyLadder")}</p>
            <div className="pv-daily-ladder-grid mt-4" data-testid="wallet-daily-ladder">
              {ladder.map((step) => (
                <div
                  key={step.day}
                  className={`pv-daily-ladder-card rounded-[1rem] border ${
                    step.isActive
                      ? "border-[var(--pv-brand)] bg-[rgba(37,92,255,0.08)]"
                      : step.isBigReward
                        ? "border-amber-200 bg-amber-50/80"
                        : "border-zinc-200 bg-zinc-50/80"
                  }`}
                  data-testid={`wallet-daily-ladder-step-${step.day}`}
                >
                  <p className="pv-daily-ladder-label">
                    {t("wallet.dayLabel", { day: step.day })}
                  </p>
                  <p className="pv-daily-ladder-reward">+{step.reward}</p>
                </div>
              ))}
            </div>
            <p className="mt-4 text-sm text-zinc-600">{t("wallet.dailyLadderBody")}</p>
          </section>

          <section className="pv-panel px-5 py-5">
            <p className="pv-kicker">{t("wallet.streakMilestones")}</p>
            <div className="mt-4 space-y-3">
              {streakMilestones.map((milestone) => {
                const reached = wallet.current_streak >= milestone.streak;
                return (
                  <div key={milestone.streak} className="pv-card-muted p-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-semibold leading-snug text-zinc-900">
                          {t("wallet.milestoneLabel", { count: milestone.streak })}
                        </p>
                        <p className="text-xs text-zinc-600">{t("wallet.milestoneReward", { amount: milestone.reward })}</p>
                      </div>
                      <span
                        className={`${reached ? "pv-badge-success" : "pv-badge"} max-w-full shrink-0 whitespace-normal text-center`}
                      >
                        {reached ? t("wallet.reached") : t("wallet.upcoming")}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
            {nextMilestoneEntry ? (
              <p className="mt-4 text-sm text-zinc-600">
                {t("wallet.nextMilestone", {
                  count: nextMilestoneEntry.streak,
                  amount: nextMilestoneEntry.reward,
                })}
              </p>
            ) : null}
            <p className="mt-3 text-xs text-zinc-500">
              {t("wallet.freezeTokens")}: {formatNumber(wallet.streak_freeze_tokens, locale)}
            </p>
          </section>

          <section className="pv-panel px-5 py-5">
            <p className="pv-kicker">{t("wallet.vaultRank")}</p>
            <p className="mt-2 text-xl font-bold text-zinc-950">
              {t("wallet.rankLevelProgress", {
                level: formatNumber(wallet.rank_level, locale),
                points: formatNumber(wallet.rank_points, locale),
                threshold: formatNumber(wallet.rank_next_threshold, locale),
              })}
            </p>
            <div className="mt-3 pv-progress">
              <div
                className="pv-progress-fill"
                style={{
                  width: `${Math.max(
                    4,
                    Math.min(
                      100,
                      Math.round((wallet.rank_points / Math.max(1, wallet.rank_next_threshold)) * 100),
                    ),
                  )}%`,
                }}
              />
            </div>
            <p className="mt-3 text-sm text-zinc-600">
              {t("wallet.ownedValueGenerated", { amount: formatNumber(wallet.owned_value_generated, locale) })}
            </p>
            <p className="mt-2 text-xs text-zinc-500">{t("wallet.rankExplainer")}</p>
          </section>
        </aside>
      </div>

      <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label={t("wallet.earned")}
          value={<LmnAmount amount={wallet.total_earned} symbol={wallet.currency_symbol} state="earned" />}
          tone="positive"
        />
        <StatCard
          label={t("wallet.spent")}
          value={<LmnAmount amount={wallet.total_spent} symbol={wallet.currency_symbol} state="spent" />}
        />
        <StatCard
          label={t("store.readyToBuyCount")}
          value={<span className="pv-metric-value">{formatNumber(readyToBuyCount, locale)}</span>}
          tone="positive"
        />
        <StatCard
          label={t("wallet.purchaseHistory")}
          value={<span className="pv-metric-value">{wallet.recent_purchases.length}</span>}
        />
        <StatCard
          label={t("wallet.pendingCashback")}
          value={<span className="pv-metric-value">{formatNumber(wallet.pending_locked_rewards.length, locale)}</span>}
          tone="positive"
        />
      </section>

      {wallet.goals.length > 0 ? (
        <section className="pv-panel px-5 py-5">
          <p className="pv-kicker">{t("wallet.activeGoals")}</p>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            {wallet.goals.map((goal) => {
              const localizedGoal = localizedGoalCopy(goal, t);
              return (
                <div key={goal.key} className="pv-card-muted p-4">
                  <p className="text-xs uppercase tracking-[0.14em] text-zinc-500">{localizedGoal.layer}</p>
                  <p className="mt-2 text-sm font-semibold text-zinc-900">{localizedGoal.title}</p>
                  <p className="mt-1 text-xs text-zinc-600">{localizedGoal.description}</p>
                  <p className="mt-2 text-xs text-zinc-500">
                    {formatNumber(goal.progress, locale)}/{formatNumber(goal.target, locale)}
                  </p>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] xl:items-start">
        <section className="pv-panel px-5 py-5">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("wallet.benefitsAndBoosts")}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("wallet.benefitsAndBoosts")}</h2>
            </div>
            <LmnAmount amount={wallet.balance} symbol={wallet.currency_symbol} strong state="balance" />
          </div>
          {wallet.active_benefits.length === 0 ? (
            <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.noBenefits")}</div>
          ) : (
            <div className="mt-5 space-y-3">
              {wallet.active_benefits.map((benefit) => (
                <div key={benefit.key} className="pv-card-muted p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-zinc-900">{benefitLabel(benefit, t, locale)}</p>
                      {benefit.expires_at ? (
                        <p className="mt-1 text-xs text-zinc-500">
                          {t("wallet.premiumUntil")}: {formatDateTime(benefit.expires_at, locale)}
                        </p>
                      ) : null}
                      {typeof benefit.metadata?.reward_body === "string" ? (
                        <p className="mt-2 text-xs text-zinc-600">{String(benefit.metadata.reward_body)}</p>
                      ) : null}
                    </div>
                    <span className="pv-badge-brand">{benefitKindLabel(benefit.kind, t)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {wallet.pending_locked_rewards.length > 0 ? (
            <div className="mt-5 space-y-3">
              {wallet.pending_locked_rewards.map((reward) => (
                <div key={reward.id} className="pv-card-muted p-4">
                  <p className="text-sm font-semibold text-zinc-900">
                    {t("wallet.pendingCashbackLocked", { amount: formatNumber(reward.amount, locale) })}
                  </p>
                  <p className="mt-1 text-xs text-zinc-600">
                    {t("wallet.pendingCashbackMissions", {
                      completed: formatNumber(reward.completed_mission_count, locale),
                      required: formatNumber(reward.required_mission_count, locale),
                    })}
                    {reward.unlock_by
                      ? ` · ${t("wallet.pendingCashbackUnlockBy", {
                          date: formatDateTime(reward.unlock_by, locale),
                        })}`
                      : ""}
                  </p>
                </div>
              ))}
            </div>
          ) : null}
        </section>

        <section className="pv-panel px-5 py-5">
          <div className="pv-section-head">
            <div className="pv-section-copy">
              <p className="pv-kicker">{t("wallet.latestPurchases")}</p>
              <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("wallet.latestPurchases")}</h2>
            </div>
            <Link href={APP_ROUTES.store} className="pv-inline-link">
              {t("nav.store")}
              <span aria-hidden="true">↗</span>
            </Link>
          </div>
          {wallet.recent_purchases.length === 0 ? (
            <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.noPurchases")}</div>
          ) : (
            <div className="mt-5 space-y-3">
              {wallet.recent_purchases.map((purchase: WalletPurchase) => (
                <div key={purchase.id} className="pv-card-muted p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-zinc-900">{purchase.item_title}</p>
                      <p className="mt-1 text-xs text-zinc-500">{formatDateTime(purchase.created_at, locale)}</p>
                    </div>
                    <LmnAmount amount={`-${purchase.price_paid}`} symbol={wallet.currency_symbol} state="spent" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="pv-panel px-5 py-5">
        <div className="pv-section-head">
          <div className="pv-section-copy">
            <p className="pv-kicker">{t("wallet.operationsTimeline")}</p>
            <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{t("wallet.operationsTimeline")}</h2>
          </div>
          <LmnAmount amount={wallet.balance} symbol={wallet.currency_symbol} state="balance" />
        </div>

        {wallet.recent.length === 0 ? (
          <div className="pv-empty-state mt-5 text-sm text-zinc-600">{t("wallet.empty")}</div>
        ) : (
          <div className="mt-5 space-y-3">
            {pagedRecent.map((tx: CurrencyTransaction) => (
              <div key={tx.id} className="pv-card-muted p-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <span
                      className={`mt-1 h-2.5 w-2.5 rounded-full ${
                        tx.amount > 0 ? "bg-[var(--pv-success)]" : "bg-slate-400"
                      }`}
                    />
                    <div>
                      <p className="font-semibold text-zinc-900">{reasonLabel(tx.reason, t)}</p>
                      <p className="text-xs text-zinc-500">
                        {formatDateTime(tx.created_at, locale)}
                        {tx.context ? ` · ${tx.context}` : ""}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <LmnAmount
                      amount={formatAmount(tx.amount)}
                      symbol={wallet.currency_symbol}
                      state={tx.amount > 0 ? "earned" : "spent"}
                    />
                    <p className="mt-2 text-xs text-zinc-500">
                      {t("wallet.balance")}: {tx.balance_after}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
        {wallet.recent.length > activityPageSize ? (
          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => setActivityPage((value) => Math.max(1, value - 1))}
              disabled={currentActivityPage <= 1}
              className="pv-button-secondary !w-auto disabled:opacity-60"
            >
              {t("wallet.prevPage")}
            </button>
            <p className="text-sm text-zinc-600">
              {t("wallet.pageCounter", { current: currentActivityPage, total: totalActivityPages })}
            </p>
            <button
              type="button"
              onClick={() => setActivityPage((value) => Math.min(totalActivityPages, value + 1))}
              disabled={currentActivityPage >= totalActivityPages}
              className="pv-button-secondary !w-auto disabled:opacity-60"
            >
              {t("wallet.nextPage")}
            </button>
          </div>
        ) : null}
      </section>
    </div>
  );
}

function StatCard({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: ReactNode;
  tone?: "neutral" | "positive";
}) {
  return (
    <div className={`pv-stat-card ${tone === "positive" ? "border-emerald-200/70 bg-emerald-50/60" : ""}`}>
      <p className="pv-stat-label">{label}</p>
      <div className="mt-3">{value}</div>
    </div>
  );
}
