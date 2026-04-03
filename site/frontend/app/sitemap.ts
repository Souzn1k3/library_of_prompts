import type { MetadataRoute } from "next";

import { getSiteUrl } from "@/lib/site";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = getSiteUrl();
  const paths = [
    { path: "", priority: 1, changeFrequency: "weekly" as const },
    { path: "/catalog", priority: 0.9, changeFrequency: "daily" as const },
    { path: "/learn", priority: 0.85, changeFrequency: "weekly" as const },
    { path: "/plans", priority: 0.7, changeFrequency: "monthly" as const },
    { path: "/submit", priority: 0.6, changeFrequency: "monthly" as const },
    { path: "/login", priority: 0.4, changeFrequency: "yearly" as const },
    { path: "/signup", priority: 0.5, changeFrequency: "yearly" as const },
    { path: "/dashboard", priority: 0.4, changeFrequency: "weekly" as const },
  ];

  const lastModified = new Date();

  return paths.map(({ path, priority, changeFrequency }) => ({
    url: `${base}${path}`,
    lastModified,
    changeFrequency,
    priority,
  }));
}
