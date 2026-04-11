"use client";

import { useSearchParams } from "next/navigation";

import { TelegramAuthButton } from "@/components/TelegramAuthButton";
import { useI18n } from "@/components/i18n/LanguageProvider";
import type { UserProfile } from "@/lib/types";

type ProfileTelegramCardProps = {
  user: UserProfile;
};

export function ProfileTelegramCard({ user }: ProfileTelegramCardProps) {
  const searchParams = useSearchParams();
  const { t } = useI18n();
  const isLinked = Boolean(user.telegram_user_id);
  const telegramStatus = searchParams.get("telegram");
  const telegramError = searchParams.get("telegram_error");

  const statusMessage =
    telegramStatus === "linked"
      ? t("profile.telegramLinkedSuccess")
      : telegramError === "cancelled"
        ? t("profile.telegramCancelled")
        : telegramError === "conflict"
          ? t("profile.telegramConflict")
          : telegramError === "expired"
            ? t("profile.telegramExpired")
            : telegramError === "not_configured"
              ? t("profile.telegramUnavailable")
              : telegramError
                ? t("profile.telegramFailed")
                : null;

  return (
    <section className="pv-panel px-5 py-5">
      <p className="pv-kicker">{t("profile.telegramTitle")}</p>
      <h3 className="mt-2 text-xl font-bold tracking-[-0.04em] text-zinc-950">
        {isLinked ? t("profile.telegramLinked") : t("profile.telegramNotLinked")}
      </h3>
      <p className="mt-2 text-sm text-zinc-600">{t("profile.telegramBody")}</p>

      {statusMessage ? (
        <div
          className={`mt-4 rounded-[1rem] border p-3 text-sm ${
            telegramStatus === "linked"
              ? "border-emerald-200 bg-emerald-50 text-emerald-900"
              : "border-amber-200 bg-amber-50 text-amber-900"
          }`}
        >
          {statusMessage}
        </div>
      ) : null}

      <div className="mt-4 rounded-[1rem] border border-[var(--pv-border)] bg-[var(--pv-surface-muted)] p-4">
        <p className="text-sm font-medium text-zinc-900">
          {isLinked
            ? t("profile.telegramLinkedId", { id: user.telegram_user_id ?? "" })
            : t("profile.telegramHint")}
        </p>
        {user.telegram_username ? (
          <p className="mt-2 text-sm text-zinc-600">@{user.telegram_username}</p>
        ) : null}
      </div>

      <TelegramAuthButton
        label={isLinked ? t("profile.telegramReconnect") : t("profile.telegramConnect")}
        mode="link"
        nextPath="/profile"
        variant="primary"
        className="mt-4 w-full justify-center"
      />
    </section>
  );
}
