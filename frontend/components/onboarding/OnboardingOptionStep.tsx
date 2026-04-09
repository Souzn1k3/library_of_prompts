"use client";

type OnboardingOptionStepProps = {
  title: string;
  subtitle: string;
  options: Array<{ value: string; label: string; hint: string }>;
  selected: string | null;
  onSelect: (value: string) => void;
};

export function OnboardingOptionStep({
  title,
  subtitle,
  options,
  selected,
  onSelect,
}: OnboardingOptionStepProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-semibold tracking-[-0.05em] text-zinc-900">{title}</h2>
        <p className="text-sm leading-relaxed text-zinc-600">{subtitle}</p>
      </div>
      <div className="grid gap-2">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onSelect(option.value)}
            className={`rounded-[1.35rem] border px-4 py-4 text-left transition ${
              selected === option.value
                ? "border-[var(--pv-brand)]/35 bg-[var(--pv-brand-soft)]/70 text-zinc-950 shadow-[0_16px_32px_rgba(15,91,255,0.1)]"
                : "border-zinc-200 bg-white/82 text-zinc-900 hover:-translate-y-0.5 hover:border-[var(--pv-border-strong)]"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{option.label}</p>
                <p
                  className={`mt-1 text-xs leading-relaxed ${
                    selected === option.value ? "text-zinc-700" : "text-zinc-600"
                  }`}
                >
                  {option.hint}
                </p>
              </div>
              <span
                className={`mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[10px] ${
                  selected === option.value
                    ? "border-[var(--pv-brand)] bg-white text-[var(--pv-brand)]"
                    : "border-zinc-300 text-zinc-400"
                }`}
              >
                {selected === option.value ? "✓" : ""}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
