import {
  DEFAULT_LANGUAGE,
  formatTranslation,
  getTranslation,
  languageToLocale,
  translations,
  type Language,
} from "@/lib/i18n";
import type { MissionNextStep, MissionRead, MissionStepRead } from "@/lib/types";

export type MissionPresentation = {
  mission: MissionRead;
  title: string;
  description: string | null;
  objective: string;
  completionCondition: string;
  nextStep: MissionNextStep | null;
  badgeLabel: string | null;
  steps: MissionStepRead[];
};

function hasTranslationKey(language: Language, key: string): boolean {
  return (
    translations[language][key] !== undefined ||
    translations[DEFAULT_LANGUAGE][key] !== undefined
  );
}

function translateOrFallback(language: Language, key: string, fallback: string): string {
  return hasTranslationKey(language, key) ? getTranslation(language, key) : fallback;
}

function translateOrFallbackNullable(
  language: Language,
  key: string,
  fallback: string | null,
): string | null {
  return hasTranslationKey(language, key) ? getTranslation(language, key) : fallback;
}

function localizeStep(
  language: Language,
  missionSlug: string,
  step: MissionStepRead,
  index: number,
): MissionStepRead {
  return {
    ...step,
    title: translateOrFallback(
      language,
      `missions.catalog.${missionSlug}.steps.${index}.title`,
      step.title,
    ),
    description: translateOrFallbackNullable(
      language,
      `missions.catalog.${missionSlug}.steps.${index}.description`,
      step.description ?? null,
    ),
  };
}

function getPendingStep(steps: MissionStepRead[]): MissionStepRead | null {
  return steps.find((step) => step.status !== "completed") ?? steps[0] ?? null;
}

function localizeNextStep(
  language: Language,
  mission: MissionRead,
  steps: MissionStepRead[],
): MissionNextStep | null {
  if (!mission.next_step) {
    return null;
  }

  const pendingStep = getPendingStep(steps);
  const nextStep = mission.next_step;

  switch (nextStep.action) {
    case "open_step_prompt":
      return {
        ...nextStep,
        label: pendingStep
          ? formatTranslation(language, "missions.nextStep.tryStep", { step: pendingStep.title })
          : getTranslation(language, "missions.nextStep.tryLinkedPrompt"),
      };
    case "open_step_lesson":
      return {
        ...nextStep,
        label: pendingStep
          ? formatTranslation(language, "missions.nextStep.openLessonStep", { step: pendingStep.title })
          : getTranslation(language, "missions.nextStep.continueLesson"),
      };
    case "view_step":
      return {
        ...nextStep,
        label: pendingStep
          ? formatTranslation(language, "missions.nextStep.viewStep", { step: pendingStep.title })
          : getTranslation(language, "missions.nextStep.openMissionDetails"),
      };
    case "view_result":
      return {
        ...nextStep,
        label: getTranslation(language, "missions.nextStep.viewResult"),
      };
    case "finish_onboarding":
      return {
        ...nextStep,
        label: getTranslation(language, "missions.nextStep.finishOnboarding"),
      };
    case "open_prompt":
      return {
        ...nextStep,
        label: getTranslation(language, "missions.nextStep.tryLinkedPrompt"),
      };
    case "browse_prompts":
      return {
        ...nextStep,
        label: getTranslation(language, "missions.nextStep.browseCatalog"),
      };
    case "upgrade_for_lesson":
      return {
        ...nextStep,
        label: getTranslation(language, "missions.nextStep.unlockLesson"),
      };
    case "open_lesson":
      return {
        ...nextStep,
        label: getTranslation(language, "missions.nextStep.continueLesson"),
      };
    case "browse_lessons":
      return {
        ...nextStep,
        label: getTranslation(language, "missions.nextStep.browseLessons"),
      };
    case "details":
      return {
        ...nextStep,
        label: getTranslation(language, "missions.nextStep.openMissionDetails"),
      };
    default:
      return {
        ...nextStep,
        label: nextStep.label,
      };
  }
}

function localizeBadge(language: Language, badge: string | null): string | null {
  if (!badge) {
    return null;
  }

  return translateOrFallbackNullable(
    language,
    `missions.rewardBadge.${badge}`,
    badge.replace(/[-_]+/g, " "),
  );
}

export function getMissionPresentation(
  language: Language,
  mission: MissionRead,
): MissionPresentation {
  const title = translateOrFallback(
    language,
    `missions.catalog.${mission.slug}.title`,
    mission.title,
  );
  const description = translateOrFallbackNullable(
    language,
    `missions.catalog.${mission.slug}.description`,
    mission.description ?? null,
  );
  const objective = translateOrFallback(
    language,
    `missions.catalog.${mission.slug}.objective`,
    mission.objective,
  );
  const completionCondition = translateOrFallback(
    language,
    `missions.catalog.${mission.slug}.completion`,
    mission.completion_condition,
  );
  const steps = mission.steps.map((step, index) => localizeStep(language, mission.slug, step, index));

  return {
    mission,
    title,
    description,
    objective,
    completionCondition,
    nextStep: localizeNextStep(language, mission, steps),
    badgeLabel: localizeBadge(language, mission.reward.badge),
    steps,
  };
}

export function formatMissionDateTime(
  language: Language,
  value: string | null | undefined,
): string {
  if (!value) {
    return "";
  }

  const locale = languageToLocale(language).replace("_", "-");
  return new Date(value).toLocaleString(locale);
}
