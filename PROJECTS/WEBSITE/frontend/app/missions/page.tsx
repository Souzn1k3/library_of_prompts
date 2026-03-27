import { MissionsClient } from "@/components/MissionsClient";
import { T } from "@/components/i18n/T";

export default function MissionsPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          <T k="missions.title" />
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-zinc-600">
          <T k="missions.subtitle" />
        </p>
      </header>
      <MissionsClient />
    </div>
  );
}
