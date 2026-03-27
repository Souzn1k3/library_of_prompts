"use client";

import { useEffect } from "react";

import { trackEvent } from "@/lib/analytics";

export function PromptViewTracker({
  promptId,
  promptSlug,
  bodyLocked,
  categorySlug,
  contributorSlug,
}: {
  promptId: string;
  promptSlug: string;
  bodyLocked: boolean;
  categorySlug?: string | null;
  contributorSlug?: string | null;
}) {
  useEffect(() => {
    trackEvent({
      eventName: "prompt_viewed",
      page: `/prompt/${promptSlug}`,
      feature: "prompt_detail",
      onceKey: `prompt_viewed:${promptId}`,
      metadata: {
        prompt_id: promptId,
        prompt_slug: promptSlug,
        category_slug: categorySlug ?? null,
        contributor_slug: contributorSlug ?? null,
        body_locked: bodyLocked,
      },
    });
    if (bodyLocked) {
      trackEvent({
        eventName: "locked_content_viewed",
        page: `/prompt/${promptSlug}`,
        feature: "paywall_prompt",
        onceKey: `locked_content_viewed:${promptId}`,
        metadata: {
          prompt_id: promptId,
          prompt_slug: promptSlug,
          category_slug: categorySlug ?? null,
        },
      });
    }
  }, [promptId, promptSlug, bodyLocked, categorySlug, contributorSlug]);

  return null;
}

