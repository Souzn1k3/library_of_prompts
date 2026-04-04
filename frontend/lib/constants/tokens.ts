export const TOKEN_NAME_SINGULAR = "Token";
export const TOKEN_NAME_PLURAL = "Tokens";
export const TOKEN_SHORT_CODE = "TKN";
export const TOKEN_FORMAL_NAME = "Platform Tokens";
export const TOKEN_HELP_TEXT = "Tokens — внутренняя валюта платформы для оплаты и расчетов";

type AmountValue = number | string;

function parseAmount(value: AmountValue): number | null {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const normalized = value.replaceAll(",", "").trim();
    if (/^[+-]?\d+(\.\d+)?$/.test(normalized)) {
      const parsed = Number(normalized);
      return Number.isFinite(parsed) ? parsed : null;
    }
  }

  return null;
}

export function getTokenDisplayLabel(value: AmountValue): string {
  const parsed = parseAmount(value);
  if (parsed === null) {
    return TOKEN_NAME_PLURAL;
  }
  return Math.abs(parsed) === 1 ? TOKEN_NAME_SINGULAR : TOKEN_NAME_PLURAL;
}

export function toTokenCode(): string {
  return TOKEN_SHORT_CODE;
}

export function toTokenFormalName(): string {
  return TOKEN_FORMAL_NAME;
}
