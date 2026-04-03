import type { Metadata } from "next";

import { getSiteUrl } from "@/lib/site";

export function absoluteUrl(path: string): string {
  const base = getSiteUrl().replace(/\/$/, "");
  if (!path) return base;
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${base}${normalized}`;
}

export function buildPageMetadata(input: {
  title: string;
  description: string;
  path: string;
  type?: "website" | "article";
}): Metadata {
  const canonical = absoluteUrl(input.path);
  return {
    title: input.title,
    description: input.description,
    alternates: { canonical },
    openGraph: {
      type: input.type ?? "website",
      title: input.title,
      description: input.description,
      url: canonical,
    },
    twitter: {
      card: "summary_large_image",
      title: input.title,
      description: input.description,
    },
  };
}

