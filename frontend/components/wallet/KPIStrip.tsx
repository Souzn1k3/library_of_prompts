"use client";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { formatNumber } from "@/lib/formatters";
import { languageToIntlLocale } from "@/lib/i18n";

type KPIStripProps = {
  earned: number;
  spent: number;
  readyToBuy: number;
  purchases: number;
  cashback: number;
};

export function KPIStrip({ earned, spent, readyToBuy, purchases, cashback }: KPIStripProps) {
  const { t, language } = useI18n();
  const locale = languageToIntlLocale(language);

  return (
    <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
      <KpiCell
        label={t("wallet.earned")}
        value={`${formatNumber(earned, locale)} ${TOKEN_SHORT_CODE}`}
        tone="positive"
      />
      <KpiCell
        label={t("wallet.spent")}
        value={`${formatNumber(spent, locale)} ${TOKEN_SHORT_CODE}`}
      />
      <KpiCell
        label={t("store.readyToBuyCount")}
        value={formatNumber(readyToBuy, locale)}
        tone="positive"
      />
      <KpiCell
        label={t("wallet.purchaseHistory")}
        value={formatNumber(purchases, locale)}
      />
      <KpiCell
        label={t("wallet.pendingCashback")}
        value={`${formatNumber(cashback, locale)} ${TOKEN_SHORT_CODE}`}
        tone="positive"
      />
    </section>
  );
}

function KpiCell({
  label,
  value,
  tone = "neutral",
}: {
  label: string;
  value: string;
  tone?: "neutral" | "positive";
}) {
  return (
    <div
      className={`h-[72px] rounded-2xl border px-4 py-3 ${
        tone === "positive"
          ? "border-emerald-200/75 bg-emerald-50/70"
          : "border-[rgba(15,23,42,0.08)] bg-white/85"
      }`}
    >
      <p className="text-[0.64rem] font-semibold uppercase tracking-[0.14em] text-zinc-500">{label}</p>
      <p className="mt-2 text-lg font-bold tracking-[-0.03em] text-zinc-950">{value}</p>
    </div>
  );
}
