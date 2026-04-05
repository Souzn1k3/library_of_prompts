"use client";

export function getInitials(value: string) {
  const parts = value
    .split(/\s+/)
    .map((chunk) => chunk.trim())
    .filter(Boolean);

  if (parts.length === 0) {
    return "PV";
  }

  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
}

export function truncateWithEllipsis(value: string, maxChars: number) {
  const normalized = value.trim();
  if (!normalized) return normalized;
  if (normalized.length <= maxChars) return normalized;
  if (maxChars <= 1) return "…";
  return `${normalized.slice(0, maxChars - 1).trimEnd()}…`;
}
