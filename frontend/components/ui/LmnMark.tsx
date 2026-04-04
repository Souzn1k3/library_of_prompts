import { TokenIcon, type TokenTone } from "@/components/ui/TokenIcon";

export type LmnTone = TokenTone;

export function LmnMark({
  size = 20,
  className,
  label,
  tone = "balance",
}: {
  size?: number;
  className?: string;
  label?: string;
  tone?: LmnTone;
}) {
  return <TokenIcon size={size} className={className} label={label} tone={tone} />;
}
