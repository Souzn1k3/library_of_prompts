import { TOKEN_SHORT_CODE } from "@/lib/constants/tokens";
import { humanizeSnakeCase } from "@/lib/formatters";
import type { TranslationKey } from "@/lib/i18n";

import type { WalletTranslate } from "./walletPresentationTypes";

export function formatSignedAmount(amount: number): string {
  const sign = amount > 0 ? "+" : "";
  return `${sign}${amount}`;
}

export function reasonLabel(reason: string, t: WalletTranslate): string {
  const key = `wallet.transaction.reason.${reason}` as TranslationKey;
  const translated = t(key);
  return translated === key ? humanizeSnakeCase(reason) : translated;
}

export function formatBalanceDelta(amount: number): string {
  return `${formatSignedAmount(amount)} ${TOKEN_SHORT_CODE}`;
}
