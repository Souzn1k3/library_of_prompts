import { CSSProperties, useId } from "react";

export type LmnTone = "balance" | "neutral" | "earned" | "spent";

const LMN_TONE_PALETTES: Record<
  Exclude<LmnTone, "neutral">,
  {
    outerStart: string;
    outerEnd: string;
    coreStart: string;
    coreEnd: string;
    seamStart: string;
    seamEnd: string;
  }
> = {
  balance: {
    outerStart: "#FFF3BA",
    outerEnd: "#F59E0B",
    coreStart: "#FFF8E1",
    coreEnd: "#FDBA2C",
    seamStart: "#FFFFFF",
    seamEnd: "#FFF0A6",
  },
  earned: {
    outerStart: "#D7FFF2",
    outerEnd: "#3ECF9A",
    coreStart: "#F2FFF9",
    coreEnd: "#76E2BC",
    seamStart: "#FFFFFF",
    seamEnd: "#D8FFF4",
  },
  spent: {
    outerStart: "#FFE0BF",
    outerEnd: "#F97316",
    coreStart: "#FFF2E5",
    coreEnd: "#FB923C",
    seamStart: "#FFF9F5",
    seamEnd: "#FFE1C7",
  },
};

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
  const outerGradientId = useId();
  const coreGradientId = useId();
  const seamGradientId = useId();
  const palette = LMN_TONE_PALETTES[tone === "neutral" ? "balance" : tone];
  const style = { "--lmn-size": `${size}px` } as CSSProperties;

  return (
    <span
      className={`pv-lmn-mark ${className ?? ""}`.trim()}
      style={style}
      data-tone={tone}
      aria-hidden={label ? undefined : true}
      role={label ? "img" : undefined}
      aria-label={label}
    >
      <svg viewBox="0 0 48 48" className="h-full w-full" fill="none">
        <defs>
          <linearGradient id={outerGradientId} x1="11" x2="37" y1="8" y2="40" gradientUnits="userSpaceOnUse">
            <stop stopColor={palette.outerStart} />
            <stop offset="1" stopColor={palette.outerEnd} />
          </linearGradient>
          <linearGradient id={coreGradientId} x1="16" x2="32" y1="12" y2="38" gradientUnits="userSpaceOnUse">
            <stop stopColor={palette.coreStart} />
            <stop offset="1" stopColor={palette.coreEnd} />
          </linearGradient>
          <linearGradient id={seamGradientId} x1="24" x2="24" y1="10" y2="38" gradientUnits="userSpaceOnUse">
            <stop stopColor={palette.seamStart} />
            <stop offset="1" stopColor={palette.seamEnd} />
          </linearGradient>
        </defs>
        <path
          d="M24 4.5 36.9 11.9 39.9 24 36.9 36.1 24 43.5 11.1 36.1 8.1 24 11.1 11.9Z"
          fill={`url(#${outerGradientId})`}
        />
        <path
          d="M24 8.6 33.2 13.8 35.4 24 33.2 34.2 24 39.4 14.8 34.2 12.6 24 14.8 13.8Z"
          fill={`url(#${coreGradientId})`}
        />
        <path d="M24 8.6 33.2 13.8 24 24 14.8 13.8Z" fill="white" opacity="0.22" />
        <path d="M24 39.4 33.2 34.2 24 24 14.8 34.2Z" fill="#8A5A12" opacity="0.15" />
        <path d="M14.8 13.8 24 24 14.8 34.2 12.6 24Z" fill="white" opacity="0.08" />
        <path d="M33.2 13.8 24 24 33.2 34.2 35.4 24Z" fill="#6B460C" opacity="0.1" />
        <path
          d="M24 11.8v24.4"
          stroke={`url(#${seamGradientId})`}
          strokeLinecap="round"
          strokeWidth="2.5"
        />
        <path
          d="M18.6 19.1 24 24l5.4-4.9"
          stroke="white"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2.2"
          opacity="0.88"
        />
        <path
          d="M18.6 28.9 24 24l5.4 4.9"
          stroke="white"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="2.2"
          opacity="0.58"
        />
      </svg>
    </span>
  );
}
