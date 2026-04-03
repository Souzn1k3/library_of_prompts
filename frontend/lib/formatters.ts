export function formatNumber(value: number, locale: string): string {
  return new Intl.NumberFormat(locale).format(value);
}

export function formatDateTime(value: string | Date, locale: string): string {
  const parsed = value instanceof Date ? value : new Date(value);
  return parsed.toLocaleString(locale);
}

export function formatDate(
  value: string | Date,
  locale: string,
  options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "short",
    day: "numeric",
  },
): string {
  const parsed = value instanceof Date ? value : new Date(value);
  return parsed.toLocaleDateString(locale, options);
}

export function formatMultiplier(
  value: number,
  locale: string,
  options: Intl.NumberFormatOptions = { minimumFractionDigits: 1, maximumFractionDigits: 1 },
): string {
  return new Intl.NumberFormat(locale, options).format(value);
}

export function humanizeSnakeCase(value: string): string {
  return value.replaceAll("_", " ");
}
