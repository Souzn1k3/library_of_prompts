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
    <div className="space-y-3">
      <div>
        <h2 className="text-xl font-semibold tracking-[-0.03em] text-zinc-900">{title}</h2>
        <p className="text-sm leading-relaxed text-zinc-600">{subtitle}</p>
      </div>
      <div className="grid gap-2">
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onSelect(option.value)}
            className={`rounded-[1.25rem] border px-4 py-4 text-left transition ${
              selected === option.value
                ? "border-[var(--pv-brand)] bg-[linear-gradient(135deg,var(--pv-brand),#4d7dff)] text-white shadow-[0_18px_34px_rgba(37,92,255,0.2)]"
                : "border-zinc-200 bg-white text-zinc-900 hover:-translate-y-0.5 hover:border-[var(--pv-border-strong)]"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{option.label}</p>
                <p
                  className={`mt-1 text-xs leading-relaxed ${
                    selected === option.value ? "text-zinc-200" : "text-zinc-600"
                  }`}
                >
                  {option.hint}
                </p>
              </div>
              <span
                className={`mt-0.5 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[10px] ${
                  selected === option.value
                    ? "border-white/60 bg-white/15 text-white"
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
