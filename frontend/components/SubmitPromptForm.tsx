"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { useI18n } from "@/components/i18n/LanguageProvider";
import {
  ApiRequestError,
  fetchCategories,
  fetchPromptDiscoveryFilters,
} from "@/lib/api";
import { trackEvent } from "@/lib/analytics";
import { submitPrompt } from "@/lib/client-api";
import {
  getDifficultyTranslationKey,
  getOutputTypeTranslationKey,
  getTechniqueTranslationKey,
} from "@/lib/i18n";
import type { Category, PromptDiscoveryFilters } from "@/lib/types";

const TECHNIQUES = ["zero_shot", "few_shot", "chain_of_thought", "other"] as const;

export function SubmitPromptForm() {
  const router = useRouter();
  const { status } = useAuth();
  const { t, language } = useI18n();
  const [categories, setCategories] = useState<Category[]>([]);
  const [discoveryFilters, setDiscoveryFilters] = useState<PromptDiscoveryFilters>({
    use_cases: [],
    model_compatibility: [],
    tags: [],
    difficulties: [],
    output_types: [],
    sorts: [],
  });
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [bootstrapLoading, setBootstrapLoading] = useState(true);
  const [bootstrapError, setBootstrapError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    async function load() {
      setBootstrapLoading(true);
      setBootstrapError(null);
      try {
        const [categoryRows, filterRows] = await Promise.all([
          fetchCategories(null, language),
          fetchPromptDiscoveryFilters(null, language),
        ]);
        setCategories(categoryRows as Category[]);
        setDiscoveryFilters(filterRows as PromptDiscoveryFilters);
      } catch {
        setCategories([]);
        setDiscoveryFilters({
          use_cases: [],
          model_compatibility: [],
          tags: [],
          difficulties: [],
          output_types: [],
          sorts: [],
        });
        setBootstrapError(t("submit.optionsLoadFailed"));
      } finally {
        setBootstrapLoading(false);
      }
    }
    load();
  }, [language, reloadToken, t]);

  async function onSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setPending(true);
    const fd = new FormData(e.currentTarget);
    try {
      const selectedUseCases = fd.getAll("use_cases").map((v) => String(v));
      const selectedModels = fd.getAll("model_compatibility").map((v) => String(v));
      const selectedTags = fd.getAll("tags").map((v) => String(v));
      const result = await submitPrompt({
        slug: String(fd.get("slug") ?? ""),
        title: String(fd.get("title") ?? ""),
        body: String(fd.get("body") ?? ""),
        summary: String(fd.get("summary") ?? "") || null,
        category_id: String(fd.get("category_id") ?? ""),
        technique: String(fd.get("technique") ?? "other"),
        difficulty:
          (String(fd.get("difficulty") ?? "") as "beginner" | "intermediate" | "advanced" | "") || null,
        output_type:
          (String(fd.get("output_type") ?? "") as "text" | "code" | "structured" | "") || null,
        use_cases: selectedUseCases,
        model_compatibility: selectedModels,
        tags: selectedTags,
        price_rub: Number(String(fd.get("price_rub") ?? "")) || null,
      });
      trackEvent({
        eventName: "submission_form_submitted",
        page: typeof window !== "undefined" ? window.location.pathname : "/submit",
        feature: "contributor_submission",
        onceKey: `submission_form_submitted:${result.id}`,
        metadata: {
          prompt_id: result.id,
          prompt_slug: result.slug,
          moderation_state: result.moderation_state,
          auto_approved: Boolean(result.auto_approved),
          use_case_count: selectedUseCases.length,
          model_count: selectedModels.length,
          tag_count: selectedTags.length,
        },
      });
      const sp = new URLSearchParams();
      sp.set("submitted", "1");
      if (result.auto_approved) {
        sp.set("autoApproved", "1");
      }
      router.push(`/dashboard?${sp.toString()}`);
    } catch (err) {
      setError(err instanceof ApiRequestError ? err.message : t("submit.failed"));
    } finally {
      setPending(false);
    }
  }

  if (status === "loading") {
    return <p className="text-sm text-zinc-500">{t("dashboard.loading")}</p>;
  }

  if (status === "unauthenticated") {
    return (
      <div className="rounded-[1.25rem] border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        <p>{t("submit.authRequired")}</p>
        <div className="mt-3 flex flex-wrap gap-3">
          <Link href="/login" className="font-medium text-amber-950 underline">
            {t("nav.login")}
          </Link>
          <Link href="/signup" className="font-medium text-amber-950 underline">
            {t("nav.signup")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <form className="space-y-5" onSubmit={onSubmit}>
      {error ? (
        <div className="rounded-[1rem] border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {error}
        </div>
      ) : null}

      {bootstrapError ? (
        <div className="space-y-2 rounded-[1rem] border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <p>{bootstrapError}</p>
          <button
            type="button"
            onClick={() => setReloadToken((value) => value + 1)}
            className="rounded-full border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-900 transition hover:border-amber-400"
          >
            {t("submit.retryLoadingOptions")}
          </button>
        </div>
      ) : null}

      <div className="pv-form-card space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div className="pv-field md:col-span-2">
            <label className="pv-label" htmlFor="title">
              {t("submit.titleLabel")}
            </label>
            <input id="title" name="title" required className="pv-input" />
          </div>

          <div className="pv-field">
            <label className="pv-label" htmlFor="slug">
              {t("submit.slugLabel")}
            </label>
            <input id="slug" name="slug" required className="pv-input" placeholder={t("submit.slugPlaceholder")} />
          </div>

          <div className="pv-field">
            <label className="pv-label" htmlFor="category_id">
              {t("submit.categoryLabel")}
            </label>
            <select
              id="category_id"
              name="category_id"
              required
              disabled={bootstrapLoading || categories.length === 0}
              className="pv-select"
              defaultValue=""
            >
              <option value="" disabled>
                {t("submit.categoryPlaceholder")}
              </option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          <div className="pv-field">
            <label className="pv-label" htmlFor="technique">
              {t("submit.techniqueLabel")}
            </label>
            <select id="technique" name="technique" className="pv-select" defaultValue="other">
              {TECHNIQUES.map((technique) => (
                <option key={technique} value={technique}>
                  {t(getTechniqueTranslationKey(technique))}
                </option>
              ))}
            </select>
          </div>

          <div className="pv-field md:col-span-2">
            <label className="pv-label" htmlFor="summary">
              {t("submit.summaryLabel")}
            </label>
            <input id="summary" name="summary" className="pv-input" />
          </div>

          <div className="pv-field">
            <label className="pv-label" htmlFor="price_rub">
              Price in RUB (optional)
            </label>
            <input
              id="price_rub"
              name="price_rub"
              type="number"
              min={0}
              max={4999}
              className="pv-input"
              placeholder="0 for free"
            />
            <p className="mt-1 text-xs text-zinc-500">
              Paid prompts become marketplace items. Buyers can unlock with money or Lumens.
            </p>
          </div>
        </div>
      </div>

      <details className="pv-details">
        <summary>{t("submit.advancedOptions")}</summary>
        <p className="mt-2 pv-hint-badge">Подсказка</p>
        <p className="mt-1 text-sm text-zinc-600">{t("submit.advancedOptionsHint")}</p>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="pv-field">
            <label className="pv-label" htmlFor="difficulty">
              {t("submit.difficultyLabel")}
            </label>
            <select id="difficulty" name="difficulty" defaultValue="" className="pv-select">
              <option value="">{t("submit.notSpecified")}</option>
              {(discoveryFilters.difficulties.length
                ? discoveryFilters.difficulties
                : ["beginner", "intermediate", "advanced"]
              ).map((difficulty) => (
                <option key={difficulty} value={difficulty}>
                  {t(getDifficultyTranslationKey(difficulty))}
                </option>
              ))}
            </select>
          </div>

          <div className="pv-field">
            <label className="pv-label" htmlFor="output_type">
              {t("submit.outputTypeLabel")}
            </label>
            <select id="output_type" name="output_type" defaultValue="" className="pv-select">
              <option value="">{t("submit.notSpecified")}</option>
              {(discoveryFilters.output_types.length
                ? discoveryFilters.output_types
                : ["text", "code", "structured"]
              ).map((outputType) => (
                <option key={outputType} value={outputType}>
                  {t(getOutputTypeTranslationKey(outputType))}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <MultiSelectField
            id="use_cases"
            name="use_cases"
            label={t("submit.useCasesLabel")}
            options={discoveryFilters.use_cases}
          />
          <MultiSelectField
            id="model_compatibility"
            name="model_compatibility"
            label={t("submit.modelCompatibilityLabel")}
            options={discoveryFilters.model_compatibility}
          />
          <MultiSelectField id="tags" name="tags" label={t("submit.tagsLabel")} options={discoveryFilters.tags} />
        </div>
      </details>

      <div className="pv-form-card">
        <div className="pv-field">
          <label className="pv-label" htmlFor="body">
            {t("submit.bodyLabel")}
          </label>
          <textarea id="body" name="body" required rows={12} className="pv-textarea font-mono" />
        </div>
      </div>

      <button
        type="submit"
        disabled={pending || bootstrapLoading || categories.length === 0}
        className="pv-button-primary w-full disabled:opacity-60"
      >
        {bootstrapLoading ? t("submit.loadingForm") : pending ? t("submit.submitPending") : t("submit.submitIdle")}
      </button>
    </form>
  );
}

function MultiSelectField({
  id,
  name,
  label,
  options,
}: {
  id: string;
  name: string;
  label: string;
  options: Array<{ slug: string; name: string }>;
}) {
  return (
    <div className="pv-field">
      <label className="pv-label" htmlFor={id}>
        {label}
      </label>
      <select id={id} name={name} multiple className="pv-select h-28">
        {options.map((opt) => (
          <option key={`${name}-${opt.slug}`} value={opt.slug}>
            {opt.name}
          </option>
        ))}
      </select>
    </div>
  );
}
