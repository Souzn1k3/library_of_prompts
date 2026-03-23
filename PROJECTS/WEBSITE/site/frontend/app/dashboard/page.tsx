import { DashboardClient } from "@/components/DashboardClient";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Dashboard</h1>
        <p className="max-w-2xl text-sm leading-relaxed text-zinc-600">
          Prompts you have saved for quick access. Saving requires an account and a running API.
        </p>
      </header>
      <DashboardClient />
    </div>
  );
}
