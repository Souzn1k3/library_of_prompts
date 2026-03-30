import { LmnMark, type LmnTone } from "@/components/ui/LmnMark";

function readNumericHint(amount: string | number): number | null {
  if (typeof amount === "number" && Number.isFinite(amount)) {
    return amount;
  }

  if (typeof amount === "string") {
    const normalized = amount.replaceAll(",", "").trim();
    if (/^[+-]?\d+(\.\d+)?$/.test(normalized)) {
      const parsed = Number(normalized);
      return Number.isFinite(parsed) ? parsed : null;
    }
  }

  return null;
}

function inferState(amount: string | number, strong: boolean): LmnTone {
  const numericHint = readNumericHint(amount);

  if (numericHint !== null) {
    if (numericHint > 0) return "earned";
    if (numericHint < 0) return "spent";
  }

  if (typeof amount === "string") {
    if (amount.trim().startsWith("+")) return "earned";
    if (amount.trim().startsWith("-")) return "spent";
  }

  return strong ? "balance" : "neutral";
}

export function LmnAmount({
  amount,
  symbol = "LMN",
  className,
  strong = false,
  iconSize = 20,
  state,
}: {
  amount: string | number;
  symbol?: string;
  className?: string;
  strong?: boolean;
  iconSize?: number;
  state?: LmnTone;
}) {
  const resolvedState = state ?? inferState(amount, strong);
  const markTone = resolvedState === "neutral" ? "balance" : resolvedState;
  const resolvedIconSize = strong ? Math.max(iconSize, 24) : iconSize;

  return (
    <span
      className={`${strong ? "pv-lmn-token pv-lmn-token-strong" : "pv-lmn-token"} ${className ?? ""}`.trim()}
      data-state={resolvedState}
      data-strong={strong ? "true" : "false"}
    >
      <span className="pv-lmn-token-mark">
        <LmnMark size={resolvedIconSize} label={symbol} tone={markTone} />
      </span>
      <span className="pv-lmn-token-copy">
        <span className="pv-lmn-token-meta">
          <span className="pv-lmn-token-value">
            {amount}
          </span>
          <span className="pv-lmn-token-code">{symbol}</span>
        </span>
      </span>
      <span className="pv-lmn-token-glow" aria-hidden="true" />
    </span>
  );
}
