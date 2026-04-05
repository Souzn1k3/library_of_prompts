"use client";

import {
  getTechniqueTranslationKey,
  type TranslationKey,
} from "@/lib/i18n";
import type { Category } from "@/lib/types";
import { TECHNIQUES } from "@/components/submit/constants";

type Translate = (
  key: TranslationKey,
  params?: Record<string, string | number | null | undefined>,
) => string;

type SubmitPromptBasicFieldsProps = {
  categories: Category[];
  bootstrapLoading: boolean;
  t: Translate;
};

export function SubmitPromptBasicFields({
  categories,
  bootstrapLoading,
  t,
}: SubmitPromptBasicFieldsProps) {
  return (
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
          <input
            id="slug"
            name="slug"
            required
            className="pv-input"
            placeholder={t("submit.slugPlaceholder")}
          />
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
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
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
            {t("submit.priceRubLabel")}
          </label>
          <input
            id="price_rub"
            name="price_rub"
            type="number"
            min={0}
            max={4999}
            className="pv-input"
            placeholder={t("submit.priceRubPlaceholder")}
          />
          <p className="mt-1 text-xs text-zinc-500">{t("submit.priceRubHint")}</p>
        </div>
      </div>
    </div>
  );
}

