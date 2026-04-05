"use client";

type SelectOption = {
  value: string;
  label: string;
};

export function CatalogSelectField({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="pv-card-muted space-y-2 p-3">
      <label className="pv-label">{label}</label>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="pv-select"
      >
        {options.map((option) => (
          <option key={`${label}-${option.value || "all"}`} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export function CatalogMultiSelectField({
  label,
  options,
  selected,
  onChange,
}: {
  label: string;
  options: Array<{ slug: string; name: string }>;
  selected: string[];
  onChange: (values: string[]) => void;
}) {
  return (
    <div className="pv-card-muted space-y-2 p-3">
      <label className="pv-label">{label}</label>
      <select
        multiple
        value={selected}
        onChange={(event) => {
          const values = Array.from(event.target.selectedOptions).map((item) => item.value);
          onChange(values);
        }}
        className="pv-select h-32"
      >
        {options.map((option) => (
          <option key={`${label}-${option.slug}`} value={option.slug}>
            {option.name}
          </option>
        ))}
      </select>
    </div>
  );
}
