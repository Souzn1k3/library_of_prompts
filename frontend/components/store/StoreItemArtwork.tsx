"use client";

import type { CSSProperties } from "react";

import type { StoreItem } from "@/lib/types";

type StoreItemArtworkProps = {
  item: StoreItem;
  title: string;
};

const PALETTES = [
  { from: "#2563eb", to: "#1d4ed8", accent: "#93c5fd" },
  { from: "#0f766e", to: "#0d9488", accent: "#5eead4" },
  { from: "#7c3aed", to: "#5b21b6", accent: "#c4b5fd" },
  { from: "#be185d", to: "#9f1239", accent: "#f9a8d4" },
  { from: "#ea580c", to: "#c2410c", accent: "#fdba74" },
  { from: "#0f172a", to: "#1e293b", accent: "#94a3b8" },
];

function hashText(value: string): number {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash;
}

function monogramFromTitle(title: string): string {
  const cleaned = title
    .replace(/[^0-9A-Za-zА-Яа-яЁё\s-]/g, " ")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (cleaned.length === 0) return "PV";
  if (cleaned.length === 1) {
    return cleaned[0].slice(0, 2).toUpperCase();
  }
  return `${cleaned[0][0] ?? ""}${cleaned[1][0] ?? ""}`.toUpperCase();
}

export function StoreItemArtwork({ item, title }: StoreItemArtworkProps) {
  const palette = PALETTES[hashText(item.slug) % PALETTES.length];
  const monogram = monogramFromTitle(title);
  const style = {
    "--pv-store-art-from": palette.from,
    "--pv-store-art-to": palette.to,
    "--pv-store-art-accent": palette.accent,
  } as CSSProperties;

  return (
    <div className="pv-store-artwork" style={style} aria-hidden="true">
      <div className="pv-store-artwork-noise" />
      <div className="pv-store-artwork-mark">{monogram}</div>
      <div className="pv-store-artwork-title">{item.slug.replace(/-/g, " ").slice(0, 24)}</div>
    </div>
  );
}
