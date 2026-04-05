"use client";

import { MultiSelectField } from "@/components/submit/MultiSelectField";
import {
  getDifficultyTranslationKey,
  getOutputTypeTranslationKey,
  type TranslationKey,
} from "@/lib/i18n";
import type { PromptDiscoveryFilters } from "@/lib/types";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type SubmitPromptAdvancedFieldsProps = {
  discoveryFilters: PromptDiscoveryFilters;
  t: Translate;
};

export function SubmitPromptAdvancedFields({
  discoveryFilters,
  t,
}: SubmitPromptAdvancedFieldsProps) {
  const difficultyOptions = discoveryFilters.difficulties.length
    ? discoveryFilters.difficulties
    : ["beginner", "intermediate", "advanced"];
  const outputTypeOptions = discoveryFilters.output_types.length
    ? discoveryFilters.output_types
    : ["text", "code", "structured"];

  return (
    <details className="pv-details">
      <summary>{t("submit.advancedOptions")}</summary>
      <p className="mt-2 pv-hint-badge">{t("common.hintBadge")}</p>
      <p className="mt-1 text-sm text-zinc-600">{t("submit.advancedOptionsHint")}</p>

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="pv-field">
          <label className="pv-label" htmlFor="difficulty">
            {t("submit.difficultyLabel")}
          </label>
          <select id="difficulty" name="difficulty" defaultValue="" className="pv-select">
            <option value="">{t("submit.notSpecified")}</option>
            {difficultyOptions.map((difficulty) => (
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
            {outputTypeOptions.map((outputType) => (
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
        <MultiSelectField
          id="tags"
          name="tags"
          label={t("submit.tagsLabel")}
          options={discoveryFilters.tags}
        />
      </div>
    </details>
  );
}

