import type { ScenarioDefinition } from "../../types";

export type PromptStageScenarioInput = {
  promptSlug: string;
  title: string;
  summary: string;
  category: "utility" | "learning" | "productivity" | "entertainment" | "growth";
  bodyLocked: boolean;
  language: "en" | "ru" | "tt";
};

function localizedCopy(language: "en" | "ru" | "tt") {
  if (language === "ru" || language === "tt") {
    return {
      liveResultKicker: "Живой результат сценария",
      liveResultSubtitle: "Сначала вы видите итог AI-работы. Ниже — полный сценарий и доступ к его логике.",
      controlKicker: "Сценарий в действии",
      controlTitle: "Попробуйте на своей задаче",
      inputPlaceholder: "Опишите вашу задачу в 1-2 предложениях, чтобы адаптировать результат.",
      modeLabel: "Глубина результата",
      modeDetailed: "Подробно",
      modeConcise: "Кратко",
      refreshResult: "Обновить результат",
      lockedTitle: "Полный сценарий закрыт",
      lockedBody: "Free-пользователь видит результат и демо. PRO открывает полный blueprint, копирование и кастомизацию.",
      unlockCta: "Разблокировать сценарий (PRO)",
      telegramCta: "Продолжить в Telegram-боте",
      unlockedTitle: "Полный сценарий доступен",
      unlockedBody: "Вы можете копировать и адаптировать сценарий под свои данные прямо сейчас.",
      runNow: "Запустить сценарий",
      boostAction: "Купить +3 запуска за Tokens",
      demoRunsLeft: "Осталось демо-запусков: {{state.global.demo_status.remaining_runs}}",
      demoUnlimited: "PRO: лимитов на запуски нет",
      bonusRunsLeft: "Бонусных запусков осталось: {{state.global.demo_status.bonus_runs_remaining}}",
      demoCapReached: "Лимит демо-запусков достигнут. Перейдите на PRO.",
    };
  }

  return {
    liveResultKicker: "Live scenario output",
    liveResultSubtitle: "You see the AI result first. The full scenario logic is available below.",
    controlKicker: "Scenario in action",
    controlTitle: "Try it on your task",
    inputPlaceholder: "Describe your task in 1-2 sentences to adapt the output.",
    modeLabel: "Output depth",
    modeDetailed: "Detailed",
    modeConcise: "Concise",
    refreshResult: "Refresh output",
    lockedTitle: "Full scenario is locked",
    lockedBody: "Free users get result preview and demo. PRO unlocks full blueprint, copying, and customization.",
    unlockCta: "Unlock scenario (PRO)",
    telegramCta: "Continue in Telegram bot",
    unlockedTitle: "Full scenario is available",
    unlockedBody: "You can copy and customize this scenario right now.",
    runNow: "Run scenario",
    boostAction: "Buy +3 runs with Tokens",
    demoRunsLeft: "Demo runs left: {{state.global.demo_status.remaining_runs}}",
    demoUnlimited: "PRO: unlimited runs",
    bonusRunsLeft: "Bonus runs left: {{state.global.demo_status.bonus_runs_remaining}}",
    demoCapReached: "Demo run cap reached. Upgrade to PRO.",
  };
}

export function buildPromptStageScenarioDefinition(input: PromptStageScenarioInput): ScenarioDefinition {
  const copy = localizedCopy(input.language);
  const bodyLockTitle = input.bodyLocked ? copy.lockedTitle : copy.unlockedTitle;
  const bodyLockBody = input.bodyLocked ? copy.lockedBody : copy.unlockedBody;

  return {
    id: `prompt-stage:${input.promptSlug}`,
    type: "ai",
    version: 3,
    title: input.title,
    description: input.summary,
    layout: {
      panels: [
        {
          id: "prompt-stage-hero",
          kind: "hero",
          renderer: "dom",
          kicker: copy.liveResultKicker,
          title: input.title,
          subtitle: copy.liveResultSubtitle,
        },
        {
          id: "prompt-stage-output",
          kind: "section",
          renderer: "hybrid",
          title: "{{state.global.prompt.title}}",
          subtitle: "{{state.global.prompt.summary}}",
          children: [
            {
              id: "prompt-stage-stream",
              kind: "stream",
              renderer: "stream",
              source: "streams.live_output",
              maxLines: 64,
              emptyText: "Run the scenario to generate output.",
            },
          ],
        },
        {
          id: "prompt-stage-controls",
          kind: "section",
          renderer: "dom",
          title: copy.controlTitle,
          subtitle: copy.controlKicker,
          children: [
            {
              id: "prompt-stage-input-form",
              kind: "form",
              renderer: "dom",
              formId: "prompt_stage",
              fieldIds: ["prompt-stage-task-input"],
              submitLabel: copy.runNow,
              submitInteractionId: "prompt-stage-run-submit",
            },
            {
              id: "prompt-stage-mode-actions",
              kind: "actions",
              renderer: "dom",
              actions: [
                {
                  id: "prompt-mode-detailed",
                  label: copy.modeDetailed,
                  tone: "secondary",
                  interactionId: "prompt-stage-set-detailed",
                },
                {
                  id: "prompt-mode-concise",
                  label: copy.modeConcise,
                  tone: "secondary",
                  interactionId: "prompt-stage-set-concise",
                },
                {
                  id: "prompt-mode-refresh",
                  label: copy.refreshResult,
                  tone: "secondary",
                  interactionId: "prompt-stage-refresh",
                },
              ],
            },
            {
              id: "prompt-stage-run-actions",
              kind: "actions",
              renderer: "dom",
              actions: [
                {
                  id: "prompt-run",
                  label: copy.runNow,
                  tone: "primary",
                  interactionId: "prompt-stage-run",
                  disabledWhen: { path: "state.global.demo_status.cap_reached", equals: true },
                },
                {
                  id: "prompt-boost",
                  label: copy.boostAction,
                  tone: "secondary",
                  interactionId: "prompt-stage-boost",
                  disabledWhen: { path: "state.global.demo_status.is_pro", equals: true },
                },
              ],
            },
            {
              id: "prompt-stage-demo-runs-left",
              kind: "text",
              renderer: "dom",
              text: copy.demoRunsLeft,
              visibleWhen: { path: "state.global.demo_status.is_pro", equals: false },
            },
            {
              id: "prompt-stage-demo-unlimited",
              kind: "text",
              renderer: "dom",
              text: copy.demoUnlimited,
              tone: "success",
              visibleWhen: { path: "state.global.demo_status.is_pro", equals: true },
            },
            {
              id: "prompt-stage-bonus-runs",
              kind: "text",
              renderer: "dom",
              text: copy.bonusRunsLeft,
              tone: "success",
              visibleWhen: { path: "state.global.demo_status.is_pro", equals: false },
            },
            {
              id: "prompt-stage-cap-message",
              kind: "text",
              renderer: "dom",
              text: copy.demoCapReached,
              tone: "warning",
              visibleWhen: { path: "state.global.demo_status.cap_reached", equals: true },
            },
            {
              id: "prompt-stage-guard-message",
              kind: "text",
              renderer: "dom",
              text: "{{state.ui.guard_message}}",
              tone: "warning",
              visibleWhen: { path: "state.ui.guard_message", exists: true },
            },
          ],
        },
        {
          id: "prompt-stage-gate",
          kind: "section",
          renderer: "dom",
          title: bodyLockTitle,
          subtitle: bodyLockBody,
          children: [
            {
              id: "prompt-stage-lock-actions",
              kind: "actions",
              renderer: "dom",
              actions: input.bodyLocked
                ? [
                    {
                      id: "prompt-stage-unlock",
                      label: copy.unlockCta,
                      tone: "primary",
                      interactionId: "prompt-stage-open-unlock",
                    },
                    {
                      id: "prompt-stage-open-telegram",
                      label: copy.telegramCta,
                      tone: "secondary",
                      interactionId: "prompt-stage-open-telegram",
                    },
                  ]
                : [
                    {
                      id: "prompt-stage-open-telegram-only",
                      label: copy.telegramCta,
                      tone: "secondary",
                      interactionId: "prompt-stage-open-telegram",
                    },
                  ],
            },
          ],
        },
      ],
    },
    inputs: {
      fields: [
        {
          id: "prompt-stage-task-input",
          formId: "prompt_stage",
          label: copy.inputPlaceholder,
          type: "textarea",
          bind: "local.prompt.task_input",
          placeholder: copy.inputPlaceholder,
          interactionId: "prompt-stage-update-input",
        },
      ],
      interactions: [
        {
          id: "prompt-stage-update-input",
          type: "input",
          source: "prompt-stage-task-input",
          emits: "form/update",
          payload: {
            bind: { from: "interaction.bind" },
            value: { from: "interaction.value" },
          },
        },
        {
          id: "prompt-stage-run-submit",
          type: "submit",
          source: "prompt_stage",
          emits: "prompt/run",
        },
        {
          id: "prompt-stage-run",
          type: "click",
          source: "prompt-stage-run",
          emits: "prompt/run",
        },
        {
          id: "prompt-stage-boost",
          type: "click",
          source: "prompt-stage-boost",
          emits: "prompt/boost",
        },
        {
          id: "prompt-stage-set-detailed",
          type: "click",
          source: "prompt-mode-detailed",
          emits: "prompt/mode-detailed",
        },
        {
          id: "prompt-stage-set-concise",
          type: "click",
          source: "prompt-mode-concise",
          emits: "prompt/mode-concise",
        },
        {
          id: "prompt-stage-refresh",
          type: "click",
          source: "prompt-mode-refresh",
          emits: "prompt/rebuild",
        },
        {
          id: "prompt-stage-open-unlock",
          type: "click",
          source: "prompt-stage-unlock",
          emits: "prompt/open-unlock",
        },
        {
          id: "prompt-stage-open-telegram",
          type: "click",
          source: "prompt-stage-open-telegram",
          emits: "prompt/open-telegram",
        },
      ],
    },
    logic: {
      entryEvents: ["app/init"],
      steps: [
        {
          id: "prompt-stage-init",
          on: "app/init",
          actions: [
            {
              kind: "invoke",
              actionId: "scenarios.fetchDemoRunStatus",
              input: {
                prompt_slug: { from: "state.global.prompt.slug" },
              },
              assign: "global.demo_status",
            },
            { kind: "set", target: "local.prompt.variation_seed", value: 0 },
            { kind: "emit", event: "prompt/rebuild" },
          ],
        },
        {
          id: "prompt-stage-form-update",
          on: "form/update",
          actions: [{ kind: "set_path", targetFrom: "bind", valueFrom: "value" }],
        },
        {
          id: "prompt-stage-mode-detailed",
          on: "prompt/mode-detailed",
          actions: [
            { kind: "set", target: "local.prompt.output_mode", value: "detailed" },
            { kind: "emit", event: "prompt/rebuild" },
          ],
        },
        {
          id: "prompt-stage-mode-concise",
          on: "prompt/mode-concise",
          actions: [
            { kind: "set", target: "local.prompt.output_mode", value: "concise" },
            { kind: "emit", event: "prompt/rebuild" },
          ],
        },
        {
          id: "prompt-stage-build-preview",
          on: "prompt/rebuild",
          actions: [
            {
              kind: "invoke",
              actionId: "scenarios.buildLiveResult",
              input: {
                language: { from: "state.global.prompt.language" },
                title: { from: "state.global.prompt.title" },
                summary: { from: "state.global.prompt.summary" },
                category: { from: "state.global.prompt.category" },
                task_input: { from: "state.local.prompt.task_input" },
                output_depth: { from: "state.local.prompt.output_mode" },
                variation_seed: { from: "state.local.prompt.variation_seed" },
              },
              assign: "global.live_result",
            },
            {
              kind: "invoke",
              actionId: "runtime.splitLines",
              input: {
                value: { from: "state.global.live_result" },
              },
              assign: "streams.live_output",
            },
            { kind: "append", target: "streams.activity", value: { template: "{{event.at}} · preview rebuilt" } },
          ],
        },
        {
          id: "prompt-stage-run",
          on: "prompt/run",
          actions: [
            {
              kind: "invoke",
              actionId: "scenarios.trackDemoRun",
              input: {
                prompt_slug: { from: "state.global.prompt.slug" },
                task_input: { from: "state.local.prompt.task_input" },
              },
              assign: "local.prompt.last_run",
            },
            {
              kind: "set",
              target: "global.demo_status",
              value: { from: "state.local.prompt.last_run.status", fallback: {} },
            },
            {
              kind: "set",
              target: "ui.guard_message",
              value: { from: "state.local.prompt.last_run.message", fallback: null },
            },
            {
              kind: "set",
              target: "local.prompt.variation_seed",
              value: { from: "event.at" },
            },
            { kind: "emit", event: "prompt/rebuild" },
          ],
        },
        {
          id: "prompt-stage-boost",
          on: "prompt/boost",
          actions: [
            {
              kind: "invoke",
              actionId: "scenarios.purchaseDemoRunBoost",
              input: {
                prompt_slug: { from: "state.global.prompt.slug" },
              },
              assign: "local.prompt.last_boost",
            },
            {
              kind: "set",
              target: "ui.guard_message",
              value: { from: "state.local.prompt.last_boost.message", fallback: null },
            },
            {
              kind: "invoke",
              actionId: "scenarios.fetchDemoRunStatus",
              input: {
                prompt_slug: { from: "state.global.prompt.slug" },
              },
              assign: "global.demo_status",
            },
          ],
        },
        {
          id: "prompt-stage-open-unlock",
          on: "prompt/open-unlock",
          actions: [
            {
              kind: "invoke",
              actionId: "runtime.navigate",
              input: {
                href: "/pricing?tier=starter",
                target: "_self",
              },
            },
          ],
        },
        {
          id: "prompt-stage-open-telegram",
          on: "prompt/open-telegram",
          actions: [
            {
              kind: "invoke",
              actionId: "runtime.navigate",
              input: {
                href: "https://t.me/prompts_souz_bot",
                target: "_blank",
              },
            },
          ],
        },
      ],
    },
    output: {
      renderer: "hybrid",
      liveUpdates: true,
      streamPath: "streams.live_output",
    },
    state: {
      variables: [
        { scope: "global", key: "prompt.slug", initial: input.promptSlug },
        { scope: "global", key: "prompt.title", initial: input.title },
        { scope: "global", key: "prompt.summary", initial: input.summary },
        { scope: "global", key: "prompt.category", initial: input.category },
        { scope: "global", key: "prompt.language", initial: input.language },
        { scope: "global", key: "demo_status", initial: {} },
        { scope: "global", key: "live_result", initial: "" },
        { scope: "local", key: "prompt.task_input", initial: "" },
        { scope: "local", key: "prompt.output_mode", initial: "detailed" },
        { scope: "local", key: "prompt.variation_seed", initial: 0 },
        { scope: "ui", key: "guard_message", initial: null },
        { scope: "streams", key: "live_output", initial: [] },
        { scope: "streams", key: "activity", initial: [] },
      ],
      persistence: {
        key: `prompt-stage-runtime:${input.promptSlug}`,
        local: true,
        server: false,
        autosaveMs: 500,
      },
      enableUndoRedo: true,
      enableReplay: true,
      resumeEvent: "app/init",
    },
    permissions: {
      defaultTier: "free",
      gates: [],
      usageLimits: [
        {
          id: "prompt_stage_run",
          event: "prompt/run",
          max: 60,
          window: "session",
        },
      ],
    },
    sandbox: {
      allowedActions: [
        "scenarios.fetchDemoRunStatus",
        "scenarios.trackDemoRun",
        "scenarios.purchaseDemoRunBoost",
        "scenarios.buildLiveResult",
        "runtime.splitLines",
        "runtime.navigate",
      ],
      maxActionMs: 6000,
      maxEventsPerMinute: 240,
    },
  };
}
