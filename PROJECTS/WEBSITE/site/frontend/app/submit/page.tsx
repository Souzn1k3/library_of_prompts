import { SubmitPromptForm } from "@/components/SubmitPromptForm";

export default function SubmitPage() {
  return (
    <div className="mx-auto max-w-xl space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Submit a prompt</h1>
        <p className="text-sm text-zinc-600">
          Creates a draft prompt in <code className="font-mono text-xs">pending</code> moderation.
          Moderators approve to publish.
        </p>
      </header>
      <SubmitPromptForm />
    </div>
  );
}
