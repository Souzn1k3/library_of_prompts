import { TokenAmount } from "@/components/ui/TokenAmount";
import type { TokenTone } from "@/components/ui/TokenIcon";

export type LmnTone = TokenTone;

export function LmnAmount({
  amount,
  className,
  strong = false,
  iconSize = 20,
  state,
  compact = false,
}: {
  amount: string | number;
  symbol?: string;
  className?: string;
  strong?: boolean;
  iconSize?: number;
  state?: LmnTone;
  compact?: boolean;
}) {
  return (
    <TokenAmount
      amount={amount}
      className={className}
      strong={strong}
      iconSize={iconSize}
      state={state}
      compact={compact}
    />
  );
}
