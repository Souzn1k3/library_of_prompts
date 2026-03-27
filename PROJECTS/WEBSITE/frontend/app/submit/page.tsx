import { SubmitPromptForm } from "@/components/SubmitPromptForm";
import { T } from "@/components/i18n/T";

export default function SubmitPage() {
  return (
    <div className="mx-auto max-w-xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          <T k="submit.pageTitle" />
        </h1>
        <p className="text-sm text-zinc-600">
          <T k="submit.pageSubtitle" />
        </p>
      </header>
      <SubmitPromptForm />
    </div>
  );
}
