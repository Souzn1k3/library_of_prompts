import { CSSProperties } from "react";

export type TokenTone = "balance" | "neutral" | "earned" | "spent";

export function TokenIcon({
  size = 20,
  className,
  label = "Token",
  tone = "balance",
}: {
  size?: number;
  className?: string;
  label?: string;
  tone?: TokenTone;
}) {
  const resolvedTone = tone === "neutral" ? "balance" : tone;
  const style = { "--token-size": `${size}px` } as CSSProperties;

  return (
    <span
      className={`pv-token-icon ${className ?? ""}`.trim()}
      style={style}
      data-tone={resolvedTone}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      <svg viewBox="0 0 24 24" className="h-full w-full" fill="none">
        <path d="M5 6.5h14" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" />
        <path d="M12 6.5v12" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" />
        <path d="M7.5 11h9" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" />
      </svg>
    </span>
  );
}
