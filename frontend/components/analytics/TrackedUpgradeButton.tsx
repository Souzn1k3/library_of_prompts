"use client";

import { useRouter } from "next/navigation";

import { trackEvent } from "@/lib/analytics";

export function TrackedUpgradeButton({
  href,
  page,
  feature,
  metadata,
  label,
  className,
}: {
  href: string;
  page: string;
  feature: string;
  metadata?: Record<string, unknown>;
  label: string;
  className?: string;
}) {
  const router = useRouter();

  function onClick() {
    trackEvent({
      eventName: "upgrade_clicked",
      page,
      feature,
      metadata: metadata ?? {},
    });
    router.push(href);
  }

  return (
    <button type="button" onClick={onClick} className={className}>
      {label}
    </button>
  );
}

