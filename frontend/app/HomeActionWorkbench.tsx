"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { useI18n } from "@/components/i18n/LanguageProvider";
import { getTechniqueTranslationKey, type Language } from "@/lib/i18n";
import type { PromptListItem } from "@/lib/types";

const MAX_VISIBLE_RESULTS = 6;
const COPY_RESET_TIMEOUT_MS = 1800;

type HomeActionWorkbenchProps = {
  initialAuthenticated: boolean;
  prompts: PromptListItem[];
  heroPromptBody: string | null;
  quickUseCases: string[];
};

export function HomeActionWorkbench({
  initialAuthenticated,
  prompts,
  heroPromptBody,
  quickUseCases,
}: HomeActionWorkbenchProps) {
  const router = useRouter();
  const { t, language } = useI18n();

  const [query, setQuery] = useState("");
  const [selectedTechnique, setSelectedTechnique] = useState<PromptListItem["technique"] | "all">("all");
  const [selectedUseCase, setSelectedUseCase] = useState<string | null>(null);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(prompts[0]?.slug ?? null);
  const [taskInput, setTaskInput] = useState("");
  const [copyState, setCopyState] = useState<"idle" | "pending" | "copied" | "error">("idle");

  const techniqueOptions = useMemo(
    () => [...new Set(prompts.map((prompt) => prompt.technique))],
    [prompts],
  );

  const filteredPrompts = useMemo(() => {
    const normalizedQuery = normalizeSearchValue(query);
    const normalizedUseCase = normalizeSearchValue(selectedUseCase);

    let next = prompts.filter((prompt) => selectedTechnique === "all" || prompt.technique === selectedTechnique);

    if (normalizedUseCase) {
      next = next.filter((prompt) => promptMatchesUseCase(prompt, normalizedUseCase));
    }

    if (!normalizedQuery) {
      return [...next].sort((a, b) => {
        const qualityDelta = (b.quality_score ?? 0) - (a.quality_score ?? 0);
        if (qualityDelta !== 0) {
          return qualityDelta;
        }
        const savesDelta = (b.save_count ?? 0) - (a.save_count ?? 0);
        if (savesDelta !== 0) {
          return savesDelta;
        }
        const copiesDelta = (b.copy_count ?? 0) - (a.copy_count ?? 0);
        if (copiesDelta !== 0) {
          return copiesDelta;
        }
        return a.title.localeCompare(b.title);
      });
    }

    return next
      .map((prompt) => ({
        prompt,
        score: scorePrompt(prompt, normalizedQuery),
      }))
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .map((item) => item.prompt);
  }, [prompts, query, selectedTechnique, selectedUseCase]);

  useEffect(() => {
    if (!filteredPrompts.length) {
      return;
    }

    if (!selectedSlug || !filteredPrompts.some((prompt) => prompt.slug === selectedSlug)) {
      setSelectedSlug(filteredPrompts[0].slug);
    }
  }, [filteredPrompts, selectedSlug]);

  useEffect(() => {
    if (copyState !== "copied") {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setCopyState("idle");
    }, COPY_RESET_TIMEOUT_MS);

    return () => window.clearTimeout(timeoutId);
  }, [copyState]);

  const selectedPrompt = useMemo(() => {
    if (!prompts.length) {
      return null;
    }

    if (selectedSlug) {
      return (
        filteredPrompts.find((prompt) => prompt.slug === selectedSlug) ??
        prompts.find((prompt) => prompt.slug === selectedSlug) ??
        filteredPrompts[0] ??
        prompts[0]
      );
    }

    return filteredPrompts[0] ?? prompts[0];
  }, [filteredPrompts, prompts, selectedSlug]);

  const visiblePrompts = filteredPrompts.slice(0, MAX_VISIBLE_RESULTS);
  const hasActiveFilters =
    query.trim().length > 0 || selectedTechnique !== "all" || Boolean(selectedUseCase);

  const readyPrompt = useMemo(() => {
    if (!selectedPrompt) {
      return "";
    }

    const selectedBody =
      heroPromptBody && prompts[0]?.slug === selectedPrompt.slug
        ? heroPromptBody
        : getPromptFallbackTemplate(language, selectedPrompt);

    const normalizedTask = taskInput.trim();
    if (!normalizedTask) {
      return selectedBody;
    }

    if (language === "ru" || language === "tt") {
      return [
        `Задача: ${normalizedTask}`,
        "",
        "Используй шаблон ниже и адаптируй его под эту задачу.",
        "",
        selectedBody,
      ].join("\n");
    }

    return [
      `Task: ${normalizedTask}`,
      "",
      "Use the template below and adapt it to this task.",
      "",
      selectedBody,
    ].join("\n");
  }, [heroPromptBody, language, prompts, selectedPrompt, taskInput]);

  async function copyReadyPrompt() {
    if (!readyPrompt.trim()) {
      return;
    }

    setCopyState("pending");
    try {
      await navigator.clipboard.writeText(readyPrompt);
      setCopyState("copied");
    } catch {
      setCopyState("error");
    }
  }

  function submitCatalogSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedPrompt) {
      router.push(`/prompt/${encodeURIComponent(selectedPrompt.slug)}`);
      return;
    }

    const params = new URLSearchParams();
    if (query.trim()) {
      params.set("q", query.trim());
    }
    const fallbackDestination = params.toString() ? `/catalog?${params.toString()}` : "/catalog";
    router.push(fallbackDestination);
  }

  function resetFilters() {
    setQuery("");
    setSelectedTechnique("all");
    setSelectedUseCase(null);
  }

  function toggleUseCase(useCase: string) {
    setSelectedUseCase((current) => (current === useCase ? null : useCase));
  }

  if (!prompts.length) {
    return (
      <section className="pv-hero px-6 py-8 sm:px-8 sm:py-10">
        <div className="space-y-4">
          <h1 className="pv-display max-w-[18ch] text-zinc-950">{t("home.entryEmptyTitle")}</h1>
          <p className="max-w-[35rem] text-sm leading-relaxed text-zinc-600">{t("home.entryEmptyBody")}</p>
          <Link href="/catalog" className="pv-button-primary w-fit">
            {t("home.entryEmptyAction")}
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section id="home-workbench" className="pv-hero px-6 py-7 sm:px-8 sm:py-9">
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] xl:items-start">
        <div className="space-y-5">
          <div className="max-w-[43rem] space-y-3">
            <p className="pv-kicker">{t("home.entryKicker")}</p>
            <h1 className="pv-display max-w-[20ch] text-zinc-950">{t("home.entryTitle")}</h1>
            <p className="text-sm leading-relaxed text-zinc-600">{t("home.entrySubtitle")}</p>
          </div>

          <form onSubmit={submitCatalogSearch} className="flex flex-col gap-3 sm:flex-row">
            <label htmlFor="home-entry-search" className="sr-only">
              {t("home.entrySearchLabel")}
            </label>
            <input
              id="home-entry-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              className="pv-input flex-1"
              placeholder={t("home.entrySearchPlaceholder")}
            />
            <button type="submit" className="pv-button-primary sm:w-auto">
              {t("home.entrySearchAction")}
            </button>
          </form>

          <div className="space-y-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                {t("home.entryFilterTechnique")}
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedTechnique("all")}
                  className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                    selectedTechnique === "all"
                      ? "border-zinc-900 bg-zinc-900 text-white"
                      : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
                  }`}
                >
                  {t("home.entryFilterAll")}
                </button>
                {techniqueOptions.map((technique) => (
                  <button
                    key={`home-technique-${technique}`}
                    type="button"
                    onClick={() => setSelectedTechnique(technique)}
                    className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                      selectedTechnique === technique
                        ? "border-zinc-900 bg-zinc-900 text-white"
                        : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
                    }`}
                  >
                    {t(getTechniqueTranslationKey(technique))}
                  </button>
                ))}
              </div>
            </div>

            {quickUseCases.length ? (
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-zinc-500">
                  {t("home.entryQuickScenarios")}
                </p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {quickUseCases.map((useCase) => (
                    <button
                      key={`home-use-case-${useCase}`}
                      type="button"
                      onClick={() => toggleUseCase(useCase)}
                      className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition ${
                        selectedUseCase === useCase
                          ? "border-[var(--pv-brand-strong)] bg-[var(--pv-brand-soft)] text-[var(--pv-brand-strong)]"
                          : "border-zinc-200 bg-white text-zinc-600 hover:border-zinc-300 hover:text-zinc-900"
                      }`}
                    >
                      {formatUseCaseLabel(useCase)}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <div className="space-y-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-zinc-900">
                {t("home.entryLiveResults", { count: filteredPrompts.length })}
              </p>
              {hasActiveFilters ? (
                <button
                  type="button"
                  onClick={resetFilters}
                  className="text-sm font-semibold text-zinc-500 transition hover:text-zinc-900"
                >
                  {t("home.entryResetFilters")}
                </button>
              ) : null}
            </div>

            {visiblePrompts.length ? (
              <div className="grid gap-2 sm:grid-cols-2">
                {visiblePrompts.map((prompt) => {
                  const isActive = selectedPrompt?.id === prompt.id;
                  return (
                    <button
                      key={`home-match-${prompt.id}`}
                      type="button"
                      onClick={() => setSelectedSlug(prompt.slug)}
                      className={`rounded-[1rem] border p-3 text-left transition ${
                        isActive
                          ? "border-[var(--pv-brand-strong)] bg-[var(--pv-brand-soft)] shadow-[0_8px_20px_rgba(37,92,255,0.12)]"
                          : "border-zinc-200 bg-white hover:border-zinc-300 hover:shadow-[0_8px_18px_rgba(15,23,42,0.07)]"
                      }`}
                    >
                      <p className="line-clamp-2 text-sm font-semibold leading-snug text-zinc-900">
                        {prompt.title}
                      </p>
                      <p className="mt-1 line-clamp-2 text-xs leading-relaxed text-zinc-600">
                        {prompt.summary ?? t("prompt.noSummary")}
                      </p>
                      <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] text-zinc-500">
                        {prompt.quality_score ? (
                          <span className="rounded-full bg-white/70 px-2 py-0.5">
                            {t("prompt.metricQuality", { count: prompt.quality_score })}
                          </span>
                        ) : null}
                        {prompt.save_count ? (
                          <span className="rounded-full bg-white/70 px-2 py-0.5">
                            {t("prompt.metricSaves", { count: prompt.save_count })}
                          </span>
                        ) : null}
                      </div>
                    </button>
                  );
                })}
              </div>
            ) : (
              <div className="rounded-[1rem] border border-dashed border-zinc-300 bg-zinc-50/85 p-4">
                <p className="text-sm font-semibold text-zinc-900">{t("home.entryNoResultsTitle")}</p>
                <p className="mt-1 text-sm leading-relaxed text-zinc-600">{t("home.entryNoResultsBody")}</p>
                <Link href="/catalog" className="pv-inline-link mt-3 text-sm">
                  {t("home.entryNoResultsAction")}
                  <span aria-hidden="true">↗</span>
                </Link>
              </div>
            )}
          </div>
        </div>

        <aside className="pv-card p-5 sm:p-6">
          {selectedPrompt ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <span className="pv-chip-brand">{t(getTechniqueTranslationKey(selectedPrompt.technique))}</span>
                {selectedPrompt.save_count ? (
                  <span className="pv-chip">{t("prompt.metricSaves", { count: selectedPrompt.save_count })}</span>
                ) : null}
                {selectedPrompt.copy_count ? (
                  <span className="pv-chip">{t("prompt.metricCopies", { count: selectedPrompt.copy_count })}</span>
                ) : null}
              </div>

              <div className="space-y-2">
                <h2 className="text-2xl font-bold tracking-[-0.04em] text-zinc-950">{selectedPrompt.title}</h2>
                <p className="text-sm leading-relaxed text-zinc-600">
                  {selectedPrompt.summary ?? t("prompt.noSummary")}
                </p>
              </div>

              <div className="space-y-2">
                <label className="pv-label" htmlFor="home-task-input">
                  {t("home.entryIntentLabel")}
                </label>
                <textarea
                  id="home-task-input"
                  value={taskInput}
                  onChange={(event) => setTaskInput(event.target.value)}
                  className="pv-textarea min-h-[98px]"
                  placeholder={t("home.entryIntentPlaceholder")}
                />
              </div>

              <div className="space-y-2">
                <p className="pv-label">{t("home.entryReadyPromptLabel")}</p>
                <pre className="max-h-[16.5rem] overflow-auto rounded-[0.95rem] border border-zinc-200 bg-zinc-50 p-3 text-xs leading-relaxed text-zinc-700 whitespace-pre-wrap">
                  {readyPrompt}
                </pre>
              </div>

              <div className="flex flex-col gap-2 sm:flex-row">
                <Link
                  href={`/prompt/${encodeURIComponent(selectedPrompt.slug)}`}
                  className="pv-button-primary sm:flex-1"
                >
                  {t("home.entryPrimaryAction")}
                </Link>
                <button
                  type="button"
                  onClick={() => void copyReadyPrompt()}
                  disabled={copyState === "pending"}
                  className="pv-button-secondary sm:w-auto disabled:opacity-60"
                >
                  {copyState === "copied"
                    ? t("home.entryCopySuccess")
                    : copyState === "pending"
                      ? t("copy.copying")
                      : t("home.entryCopyAction")}
                </button>
              </div>

              {copyState === "error" ? (
                <p className="text-sm text-red-700">{t("home.entryCopyError")}</p>
              ) : null}

              {copyState === "copied" ? (
                <div className="space-y-2 rounded-[1rem] border border-emerald-200 bg-emerald-50/80 p-3">
                  <p className="text-sm leading-relaxed text-emerald-900">{t("home.entryCopiedHint")}</p>
                  <div className="flex flex-wrap gap-2">
                    <Link
                      href={`/prompt/${encodeURIComponent(selectedPrompt.slug)}`}
                      className="rounded-full border border-emerald-300 px-3 py-1.5 text-xs font-semibold text-emerald-900 transition hover:bg-emerald-100"
                    >
                      {t("home.entryNextActionOpen")}
                    </Link>
                    <Link
                      href={initialAuthenticated ? "/dashboard" : "/signup"}
                      className="rounded-full border border-emerald-300 px-3 py-1.5 text-xs font-semibold text-emerald-900 transition hover:bg-emerald-100"
                    >
                      {t(initialAuthenticated ? "home.entryNextActionSaveAuth" : "home.entryNextActionSaveGuest")}
                    </Link>
                  </div>
                </div>
              ) : null}
            </div>
          ) : null}
        </aside>
      </div>
    </section>
  );
}

function normalizeSearchValue(value: string | null | undefined): string {
  return (value ?? "")
    .toLowerCase()
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function promptMatchesUseCase(prompt: PromptListItem, normalizedUseCase: string): boolean {
  const value = [
    ...(prompt.use_cases ?? []),
    ...(prompt.tags ?? []),
    prompt.title,
    prompt.summary ?? "",
  ]
    .join(" ")
    .toLowerCase()
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ");

  return value.includes(normalizedUseCase);
}

function scorePrompt(prompt: PromptListItem, normalizedQuery: string): number {
  const title = normalizeSearchValue(prompt.title);
  const summary = normalizeSearchValue(prompt.summary);
  const useCases = normalizeSearchValue((prompt.use_cases ?? []).join(" "));
  const tags = normalizeSearchValue((prompt.tags ?? []).join(" "));

  let score = 0;
  if (title.includes(normalizedQuery)) {
    score += 8;
  }
  if (summary.includes(normalizedQuery)) {
    score += 5;
  }
  if (useCases.includes(normalizedQuery)) {
    score += 4;
  }
  if (tags.includes(normalizedQuery)) {
    score += 3;
  }

  const queryWords = normalizedQuery.split(" ").filter(Boolean);
  for (const word of queryWords) {
    if (title.includes(word)) {
      score += 2;
    }
    if (summary.includes(word)) {
      score += 1;
    }
  }

  return score;
}

function getPromptFallbackTemplate(language: Language, prompt: PromptListItem): string {
  const isRuFamily = language === "ru" || language === "tt";
  const promptSummary = prompt.summary?.trim() || (isRuFamily ? "Нет краткого описания." : "No summary provided.");

  if (isRuFamily) {
    return [
      `Контекст: ${prompt.title}`,
      `Описание: ${promptSummary}`,
      "",
      "Сделай:",
      "1) Сначала уточни недостающие детали задачи.",
      "2) Предложи рабочую структуру решения.",
      "3) Дай финальный результат в практичном формате.",
    ].join("\n");
  }

  return [
    `Context: ${prompt.title}`,
    `Summary: ${promptSummary}`,
    "",
    "Do this:",
    "1) Ask for missing details first.",
    "2) Propose a practical solution structure.",
    "3) Return a ready-to-use final output.",
  ].join("\n");
}

function formatUseCaseLabel(useCase: string): string {
  return useCase
    .split(" ")
    .filter(Boolean)
    .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
    .join(" ");
}
