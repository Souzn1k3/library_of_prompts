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

const PRIMARY_BUTTON_CLASS = "bg-[var(--pv-brand)] hover:bg-[var(--pv-brand-strong)]";

export const STORE_KIND_TONE: Record<StoreItemKind, Required<Tone>> = {
  starter: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
    button: PRIMARY_BUTTON_CLASS,
  },
  premium_pass: {
    badge: "border border-[rgba(29,78,216,0.24)] bg-[rgba(29,78,216,0.1)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(29,78,216,0.12)]",
    button: PRIMARY_BUTTON_CLASS,
  },
  subscription_discount: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
    button: PRIMARY_BUTTON_CLASS,
  },
  boost: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
    button: PRIMARY_BUTTON_CLASS,
  },
  future: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(148,163,184,0.12)]",
    button: "bg-zinc-700 hover:bg-zinc-800",
  },
  premium_prompt_unlock: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
    button: PRIMARY_BUTTON_CLASS,
  },
  prompt_bundle: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
    button: PRIMARY_BUTTON_CLASS,
  },
};

export const MISSION_TYPE_TONE: Record<MissionType, Tone> = {
  spend_linked: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
  },
  habit: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
  },
  progress: {
    badge: "border border-[rgba(29,78,216,0.24)] bg-[rgba(29,78,216,0.1)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(29,78,216,0.12)]",
  },
  progression: {
    badge: "border border-[rgba(29,78,216,0.24)] bg-[rgba(29,78,216,0.1)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(29,78,216,0.12)]",
  },
  learning: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
  },
  action: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
  },
  streak: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
  },
  challenge: {
    badge: "border border-zinc-300 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(15,23,42,0.08)]",
  },
};
