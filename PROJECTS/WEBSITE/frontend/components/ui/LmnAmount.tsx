import { LmnMark } from "@/components/ui/LmnMark";

export function LmnAmount({
  amount,
  symbol = "LMN",
  className,
  strong = false,
  iconSize = 20,
}: {
  amount: string | number;
  symbol?: string;
  className?: string;
  strong?: boolean;
  iconSize?: number;
}) {
  return (
    <span className={`${strong ? "pv-lmn-token pv-lmn-token-strong" : "pv-lmn-token"} ${className ?? ""}`.trim()}>
      <LmnMark size={iconSize} label={symbol} />
      <span className="flex items-baseline gap-2">
        <span className={`${strong ? "text-lg" : "text-sm"} font-extrabold tracking-[-0.03em] text-[var(--pv-text)]`}>
          {amount}
        </span>
        <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">{symbol}</span>
      </span>
    </span>
  );
}
