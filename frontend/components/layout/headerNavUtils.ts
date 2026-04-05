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
