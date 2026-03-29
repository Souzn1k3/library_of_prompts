import { CSSProperties, useId } from "react";

export function LmnMark({
  size = 20,
  className,
  label,
}: {
  size?: number;
  className?: string;
  label?: string;
}) {
  const gradientId = useId();
  const style = { "--lmn-size": `${size}px` } as CSSProperties;

  return (
    <span
      className={`inline-flex h-[var(--lmn-size)] w-[var(--lmn-size)] shrink-0 items-center justify-center rounded-full bg-white/70 p-[2px] shadow-[0_12px_22px_rgba(37,92,255,0.16)] ${
        className ?? ""
      }`}
      style={style}
      aria-hidden={label ? undefined : true}
      role={label ? "img" : undefined}
      aria-label={label}
    >
      <svg viewBox="0 0 48 48" className="h-full w-full" fill="none">
        <defs>
          <linearGradient id={gradientId} x1="10" x2="40" y1="10" y2="40" gradientUnits="userSpaceOnUse">
            <stop stopColor="#255cff" />
            <stop offset="1" stopColor="#11b8a4" />
          </linearGradient>
        </defs>
        <circle cx="24" cy="24" r="22" fill={`url(#${gradientId})`} />
        <circle cx="24" cy="24" r="18.25" fill="white" opacity="0.12" />
        <path
          d="M15.5 14.75v18.5h16.75"
          stroke="white"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="4"
        />
        <path
          d="M20.25 29.25 27.75 17.75l5.5 11.5"
          stroke="white"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth="3.35"
        />
        <circle cx="33.25" cy="29.25" r="2.2" fill="white" />
      </svg>
    </span>
  );
}
