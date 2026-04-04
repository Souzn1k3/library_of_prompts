import { getTokenDisplayLabel, TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { TokenIcon, type TokenTone } from "@/components/ui/TokenIcon";

type AmountInput = number | string;

function readNumericHint(value: AmountInput): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const normalized = value.replaceAll(",", "").trim();
    if (/^[+-]?\d+(\.\d+)?$/.test(normalized)) {
      const parsed = Number(normalized);
      return Number.isFinite(parsed) ? parsed : null;
    }
  }

  return null;
}

function inferState(value: AmountInput, strong: boolean): TokenTone {
  const numericHint = readNumericHint(value);

  if (numericHint !== null) {
    if (numericHint > 0) return "earned";
    if (numericHint < 0) return "spent";
  }

  if (typeof value === "string") {
    if (value.trim().startsWith("+")) return "earned";
    if (value.trim().startsWith("-")) return "spent";
  }

  return strong ? "balance" : "neutral";
}

export function TokenAmount({
  value,
  amount,
  className,
  strong = false,
  iconSize = 20,
  state,
  compact = false,
  showIcon,
}: {
  value?: AmountInput;
  amount?: AmountInput;
  className?: string;
  strong?: boolean;
  iconSize?: number;
  state?: TokenTone;
  compact?: boolean;
  showIcon?: boolean;
}) {
  const resolvedValue = value ?? amount ?? 0;
  const resolvedState = state ?? inferState(resolvedValue, strong);
  const resolvedIconSize = strong ? Math.max(iconSize, 24) : iconSize;
  const resolvedShowIcon = showIcon ?? !compact;
  const tokenLabel = compact ? TOKEN_SHORT_CODE : getTokenDisplayLabel(resolvedValue);

  return (
    <span
      className={`${strong ? "pv-lmn-token pv-lmn-token-strong" : "pv-lmn-token"} ${className ?? ""}`.trim()}
      data-state={resolvedState}
      data-strong={strong ? "true" : "false"}
      data-compact={compact ? "true" : "false"}
    >
      {resolvedShowIcon ? (
        <span className="pv-lmn-token-mark">
          <TokenIcon size={resolvedIconSize} label={tokenLabel} tone={resolvedState} />
        </span>
      ) : null}
      <span className="pv-lmn-token-copy">
        <span className="pv-lmn-token-meta">
          <span className="pv-lmn-token-value">{resolvedValue}</span>
          <span className="pv-lmn-token-code">{tokenLabel}</span>
        </span>
      </span>
      <span className="pv-lmn-token-glow" aria-hidden="true" />
    </span>
  );
}
