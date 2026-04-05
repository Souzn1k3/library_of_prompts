"use client";

type MultiSelectFieldProps = {
  id: string;
  name: string;
  label: string;
  options: Array<{ slug: string; name: string }>;
};

export function MultiSelectField({
  id,
  name,
  label,
  options,
}: MultiSelectFieldProps) {
  return (
    <div className="pv-field">
      <label className="pv-label" htmlFor={id}>
        {label}
      </label>
      <select id={id} name={name} multiple className="pv-select h-28">
        {options.map((option) => (
          <option key={`${name}-${option.slug}`} value={option.slug}>
            {option.name}
          </option>
        ))}
      </select>
    </div>
  );
}

