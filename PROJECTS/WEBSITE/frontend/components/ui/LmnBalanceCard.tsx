import Link from "next/link";
import type { ReactNode } from "react";

import { LmnMark, type LmnTone } from "@/components/ui/LmnMark";

function formatSignedAmount(amount: number) {
  return amount > 0 ? `+${amount}` : `${amount}`;
}

export function LmnBalanceCard({
  label,
  amount,
  symbol = "LMN",
  caption,
  detail,
  actionHref,
  actionLabel,
  delta,
  change,
  className,
  tone = "balance",
  iconSize = 56,
  compact = false,
}: {
  label: ReactNode;
  amount: string | number;
  symbol?: string;
  caption?: ReactNode;
  detail?: ReactNode;
  actionHref?: string;
  actionLabel?: ReactNode;
  delta?: number | null;
  change?: "up" | "down" | null;
  className?: string;
  tone?: Exclude<LmnTone, "neutral">;
  iconSize?: number;
  compact?: boolean;
}) {
  return (
    <div
      className={`pv-lmn-balance-card ${className ?? ""}`.trim()}
      data-tone={tone}
      data-change={change ?? undefined}
      data-compact={compact ? "true" : undefined}
    >
      <div className="pv-lmn-balance-head">
        <div className="min-w-0">
          <p className="pv-lmn-balance-label">{label}</p>
          {caption ? <p className="pv-lmn-balance-caption">{caption}</p> : null}
        </div>
        <div className="pv-lmn-balance-mark">
          <LmnMark size={iconSize} label={symbol} tone={tone} />
        </div>
      </div>

      <div className="pv-lmn-balance-main">
        <span className="pv-lmn-balance-value">{amount}</span>
        <span className="pv-lmn-balance-code">{symbol}</span>
      </div>

      {detail || (delta && delta !== 0) ? (
        <div className="pv-lmn-balance-foot">
          <div className="min-w-0">
            {detail ? <div className="pv-lmn-balance-detail">{detail}</div> : null}
          </div>
          {delta && delta !== 0 ? (
            <span className="pv-lmn-balance-delta" data-direction={delta > 0 ? "up" : "down"}>
              {formatSignedAmount(delta)} {symbol}
            </span>
          ) : null}
        </div>
      ) : null}

      {actionHref && actionLabel ? (
        <div className="pv-lmn-balance-action">
          <Link href={actionHref} className="pv-lmn-balance-action-link">
            <span>{actionLabel}</span>
            <span aria-hidden="true">↗</span>
          </Link>
        </div>
      ) : null}
    </div>
  );
}
