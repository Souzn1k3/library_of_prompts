import { WalletClient } from "@/components/WalletClient";
import { T } from "@/components/i18n/T";

export default function WalletPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">
          <T k="wallet.title" />
        </h1>
        <p className="max-w-2xl text-sm leading-relaxed text-zinc-600">
          <T k="wallet.subtitle" />
        </p>
      </header>
      <WalletClient />
    </div>
  );
}
