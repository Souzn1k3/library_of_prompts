"use client";

import { useCallback, useState } from "react";

import { ApiRequestError } from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import { submitPrompt } from "@/lib/client-api";
import { APP_ROUTES } from "@/lib/constants/routes";
import type { TranslationKey } from "@/lib/i18n";
import type { Category, PromptDiscoveryFilters } from "@/lib/types";

import { buildSubmitPayload } from "@/components/submit/submitPromptPayload";
import { useSubmitPromptOptions } from "@/components/submit/useSubmitPromptOptions";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type SubmitPromptResult = Awaited<ReturnType<typeof submitPrompt>>;

type UseSubmitPromptFormArgs = {
  language: string;
  t: Translate;
  onSubmitted: (result: SubmitPromptResult) => void;
};

type UseSubmitPromptFormResult = {
  categories: Category[];
  discoveryFilters: PromptDiscoveryFilters;
  pending: boolean;
  error: string | null;
  bootstrapLoading: boolean;
  bootstrapError: string | null;
  reloadOptions: () => void;
  submitFromForm: (form: HTMLFormElement) => Promise<void>;
};

export function useSubmitPromptForm({
  language,
  t,
  onSubmitted,
}: UseSubmitPromptFormArgs): UseSubmitPromptFormResult {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const {
    categories,
    discoveryFilters,
    bootstrapLoading,
    bootstrapError,
    reloadOptions,
  } = useSubmitPromptOptions({
    language,
    t,
  });

  const submitFromForm = useCallback(
    async (form: HTMLFormElement) => {
      setError(null);
      setPending(true);

      const formData = new FormData(form);
      const { payload, selections } = buildSubmitPayload(formData);

      try {
        const result = await submitPrompt(payload);
        trackEvent({
          eventName: "submission_form_submitted",
          page: typeof window !== "undefined" ? window.location.pathname : APP_ROUTES.submit,
          feature: "contributor_submission",
          onceKey: `submission_form_submitted:${result.id}`,
          metadata: {
            prompt_id: result.id,
            prompt_slug: result.slug,
            moderation_state: result.moderation_state,
            auto_approved: Boolean(result.auto_approved),
            use_case_count: selections.selectedUseCases.length,
            model_count: selections.selectedModels.length,
            tag_count: selections.selectedTags.length,
          },
        });
        onSubmitted(result);
      } catch (requestError) {
        setError(
          requestError instanceof ApiRequestError ? requestError.message : t("submit.failed"),
        );
      } finally {
        setPending(false);
      }
    },
    [onSubmitted, t],
  );

  return {
    categories,
    discoveryFilters,
    pending,
    error,
    bootstrapLoading,
    bootstrapError,
    reloadOptions,
    submitFromForm,
  };
}
