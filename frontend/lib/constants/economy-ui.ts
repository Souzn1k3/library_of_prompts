import type { MissionType, StoreItemKind } from "@/lib/types";

export const STORE_SECTION_ORDER: StoreItemKind[] = [
  "starter",
  "boost",
  "premium_pass",
  "subscription_discount",
  "premium_prompt_unlock",
  "prompt_bundle",
  "future",
];

export const MISSION_SECTION_ORDER: MissionType[] = [
  "progress",
  "spend_linked",
  "habit",
  "progression",
  "learning",
  "action",
  "streak",
  "challenge",
];

export const STORE_SUCCESS_CLEAR_TIMEOUT_MS = 4600;
export const STORE_NEAR_MISS_ITEMS_LIMIT = 3;

export type Tone = {
  badge: string;
  glow: string;
  button?: string;
};

export const STORE_KIND_TONE: Record<StoreItemKind, Required<Tone>> = {
  starter: {
    badge: "border border-[rgba(154,105,15,0.24)] bg-[rgba(251,244,231,0.95)] text-[var(--pv-warning)]",
    glow: "bg-[rgba(154,105,15,0.12)]",
    button: "bg-[var(--pv-brand)] hover:bg-[var(--pv-brand-strong)]",
  },
  premium_pass: {
    badge: "border border-[rgba(47,111,189,0.24)] bg-[var(--pv-brand-soft)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(47,111,189,0.14)]",
    button: "bg-[var(--pv-brand)] hover:bg-[var(--pv-brand-strong)]",
  },
  subscription_discount: {
    badge: "border border-[rgba(38,122,94,0.24)] bg-[rgba(237,248,243,0.95)] text-[var(--pv-success)]",
    glow: "bg-[rgba(38,122,94,0.14)]",
    button: "bg-[var(--pv-brand)] hover:bg-[var(--pv-brand-strong)]",
  },
  boost: {
    badge: "border border-[rgba(154,105,15,0.24)] bg-[rgba(251,244,231,0.95)] text-[var(--pv-warning)]",
    glow: "bg-[rgba(154,105,15,0.14)]",
    button: "bg-[var(--pv-brand)] hover:bg-[var(--pv-brand-strong)]",
  },
  future: {
    badge: "border border-zinc-200 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(148,163,184,0.14)]",
    button: "bg-[var(--pv-brand)] hover:bg-[var(--pv-brand-strong)]",
  },
  premium_prompt_unlock: {
    badge: "border border-[rgba(47,111,189,0.24)] bg-[var(--pv-brand-soft)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(47,111,189,0.14)]",
    button: "bg-[var(--pv-brand)] hover:bg-[var(--pv-brand-strong)]",
  },
  prompt_bundle: {
    badge: "border border-[rgba(47,111,189,0.24)] bg-[var(--pv-brand-soft)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(47,111,189,0.14)]",
    button: "bg-[var(--pv-brand)] hover:bg-[var(--pv-brand-strong)]",
  },
};

export const MISSION_TYPE_TONE: Record<MissionType, Tone> = {
  spend_linked: {
    badge: "border border-[rgba(154,105,15,0.24)] bg-[rgba(251,244,231,0.95)] text-[var(--pv-warning)]",
    glow: "bg-[rgba(154,105,15,0.14)]",
  },
  habit: {
    badge: "border border-[rgba(38,122,94,0.24)] bg-[rgba(237,248,243,0.95)] text-[var(--pv-success)]",
    glow: "bg-[rgba(38,122,94,0.14)]",
  },
  progress: {
    badge: "border border-[rgba(47,111,189,0.24)] bg-[var(--pv-brand-soft)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(47,111,189,0.14)]",
  },
  progression: {
    badge: "border border-[rgba(47,111,189,0.24)] bg-[var(--pv-brand-soft)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(47,111,189,0.14)]",
  },
  learning: {
    badge: "border border-[rgba(38,122,94,0.24)] bg-[rgba(237,248,243,0.95)] text-[var(--pv-success)]",
    glow: "bg-[rgba(38,122,94,0.14)]",
  },
  action: {
    badge: "border border-[rgba(47,111,189,0.24)] bg-[var(--pv-brand-soft)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(47,111,189,0.14)]",
  },
  streak: {
    badge: "border border-[rgba(154,105,15,0.24)] bg-[rgba(251,244,231,0.95)] text-[var(--pv-warning)]",
    glow: "bg-[rgba(154,105,15,0.14)]",
  },
  challenge: {
    badge: "border border-[rgba(157,45,45,0.24)] bg-[rgba(250,237,237,0.95)] text-[var(--pv-danger)]",
    glow: "bg-[rgba(157,45,45,0.14)]",
  },
};
