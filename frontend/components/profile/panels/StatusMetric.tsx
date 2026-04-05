"use client";

type StatusMetricProps = {
  title: string;
  value: string;
  caption?: string;
};

export function StatusMetric({ title, value, caption }: StatusMetricProps) {
  return (
    <div className="rounded-[1rem] border border-zinc-200/80 bg-white p-3">
      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">{title}</p>
      <p className="mt-2 text-sm font-semibold text-zinc-900">{value}</p>
      {caption ? <p className="mt-1 text-xs text-zinc-500">{caption}</p> : null}
    </div>
  );
}

