import { CopyPromptButton } from "@/components/CopyPromptButton";

type PromptPageContentPanelProps = {
  promptId: string;
  body: string;
  bodyLocked: boolean;
  interactionMetadata: Record<string, string | null>;
};

export function PromptPageContentPanel({
  promptId,
  body,
  bodyLocked,
  interactionMetadata,
}: PromptPageContentPanelProps) {
  return (
    <section className="pv-panel px-6 py-6 sm:px-7">
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
          className={`overflow-x-auto whitespace-pre-wrap rounded-[1.25rem] border border-[var(--pv-border)] bg-white/80 p-5 font-mono text-sm leading-relaxed text-zinc-900 ${!bodyLocked ? "pr-14" : ""}`}
        >
          {body}
        </pre>
      </div>
    </section>
  );
}
