import Link from "next/link";

import { CopyPromptButton } from "@/components/CopyPromptButton";
import { getTranslation, type Language } from "@/lib/i18n";

type PromptPageContentPanelProps = {
  language: Language;
  promptId: string;
  promptSlug: string;
  body: string;
  bodyLocked: boolean;
  interactionMetadata: Record<string, string | null>;
};

export function PromptPageContentPanel({
  language,
  promptId,
  promptSlug,
  body,
  bodyLocked,
  interactionMetadata,
}: PromptPageContentPanelProps) {
  const previewBody = bodyLocked ? body.split("\n").slice(0, 14).join("\n") : body;

  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
      <div className="space-y-3">
        <div>
          <p className="pv-kicker">{getTranslation(language, "prompt.scenarioBlueprintKicker")}</p>
          <h2 className="mt-2 text-xl font-semibold tracking-[-0.03em] text-zinc-950">
            {getTranslation(language, "prompt.scenarioBlueprintTitle")}
          </h2>
          <p className="mt-2 text-sm leading-relaxed text-zinc-600">
            {bodyLocked
              ? getTranslation(language, "prompt.scenarioBlueprintLockedBody")
              : getTranslation(language, "prompt.scenarioBlueprintOpenBody")}
          </p>
        </div>

        <div className="relative">
        {!bodyLocked ? (
          <div className="absolute right-3 top-3 z-10">
            <CopyPromptButton
              promptId={promptId}
              body={body}
              metadata={interactionMetadata}
              variant="icon"
            />
          </div>
        ) : null}
        <pre
          className={`overflow-x-auto whitespace-pre-wrap rounded-[1rem] border border-[var(--pv-border)] bg-[var(--pv-surface-muted)] p-5 font-mono text-sm leading-relaxed text-zinc-900 ${!bodyLocked ? "pr-14" : ""} ${bodyLocked ? "select-none blur-[1.5px]" : ""}`}
        >
          {previewBody}
        </pre>

        {bodyLocked ? (
          <div className="absolute inset-x-4 bottom-4 rounded-[0.85rem] border border-[var(--pv-border)] bg-[var(--pv-surface-strong)] p-4">
            <p className="text-sm font-semibold text-zinc-950">
              {getTranslation(language, "prompt.scenarioLockedOverlayTitle")}
            </p>
            <p className="mt-1 text-sm leading-relaxed text-zinc-600">
              {getTranslation(language, "prompt.scenarioLockedOverlayBody")}
            </p>
            <div className="pv-action-bar pv-action-bar-start">
              <Link href="/pricing?tier=starter" className="pv-button-primary !w-auto">
                {getTranslation(language, "prompt.upgradeToUnlock")}
              </Link>
              <a
                href={`https://t.me/prompts_souz_bot?start=${encodeURIComponent(promptSlug)}`}
                target="_blank"
                rel="noreferrer"
                className="pv-button-secondary !w-auto"
              >
                {getTranslation(language, "prompt.testInTelegram")}
              </a>
            </div>
          </div>
        ) : null}
        </div>
      </div>
    </section>
  );
}
