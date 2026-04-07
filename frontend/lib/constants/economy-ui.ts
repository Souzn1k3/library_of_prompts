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
    badge: "border border-[rgba(234,88,12,0.18)] bg-[rgba(255,237,213,0.9)] text-orange-700",
    glow: "bg-[rgba(249,115,22,0.16)]",
    button:
      "bg-[linear-gradient(135deg,#f97316,#fb923c)] hover:-translate-y-0.5 hover:bg-[linear-gradient(135deg,#ea580c,#f97316)]",
  },
  premium_pass: {
    badge: "border border-[rgba(37,92,255,0.18)] bg-[rgba(37,92,255,0.1)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(37,92,255,0.16)]",
    button:
      "bg-[linear-gradient(135deg,var(--pv-brand),#4d7dff)] hover:-translate-y-0.5 hover:bg-[linear-gradient(135deg,var(--pv-brand-strong),#3968f4)]",
  },
  subscription_discount: {
    badge: "border border-[rgba(17,184,164,0.18)] bg-[rgba(17,184,164,0.12)] text-[var(--pv-accent-strong)]",
    glow: "bg-[rgba(17,184,164,0.16)]",
    button:
      "bg-[linear-gradient(135deg,var(--pv-accent),#35cbb8)] hover:-translate-y-0.5 hover:bg-[linear-gradient(135deg,var(--pv-accent-strong),#1fb9a5)]",
  },
  boost: {
    badge: "border border-[rgba(245,158,11,0.2)] bg-[rgba(254,243,199,0.65)] text-amber-800",
    glow: "bg-[rgba(245,158,11,0.18)]",
    button:
      "bg-[linear-gradient(135deg,#f59e0b,#f97316)] hover:-translate-y-0.5 hover:bg-[linear-gradient(135deg,#d97706,#ea580c)]",
  },
  future: {
    badge: "border border-zinc-200 bg-zinc-100 text-zinc-700",
    glow: "bg-[rgba(148,163,184,0.16)]",
    button: "bg-slate-600 hover:bg-slate-700",
  },
  premium_prompt_unlock: {
    badge: "border border-[rgba(99,102,241,0.16)] bg-[rgba(99,102,241,0.1)] text-indigo-700",
    glow: "bg-[rgba(99,102,241,0.16)]",
    button:
      "bg-[linear-gradient(135deg,#4f46e5,#7268ff)] hover:-translate-y-0.5 hover:bg-[linear-gradient(135deg,#4338ca,#635bff)]",
  },
  prompt_bundle: {
    badge: "border border-[rgba(99,102,241,0.16)] bg-[rgba(99,102,241,0.1)] text-indigo-700",
    glow: "bg-[rgba(99,102,241,0.16)]",
    button:
      "bg-[linear-gradient(135deg,#4f46e5,#7268ff)] hover:-translate-y-0.5 hover:bg-[linear-gradient(135deg,#4338ca,#635bff)]",
  },
};

export const MISSION_TYPE_TONE: Record<MissionType, Tone> = {
  spend_linked: {
    badge: "border border-[rgba(251,146,60,0.18)] bg-[rgba(254,215,170,0.4)] text-orange-700",
    glow: "bg-[rgba(251,146,60,0.2)]",
  },
  habit: {
    badge: "border border-[rgba(34,197,94,0.18)] bg-[rgba(187,247,208,0.35)] text-emerald-700",
    glow: "bg-[rgba(34,197,94,0.18)]",
  },
  progress: {
    badge: "border border-[rgba(37,92,255,0.18)] bg-[rgba(37,92,255,0.1)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(37,92,255,0.16)]",
  },
  progression: {
    badge: "border border-[rgba(37,92,255,0.18)] bg-[rgba(37,92,255,0.1)] text-[var(--pv-brand-strong)]",
    glow: "bg-[rgba(37,92,255,0.16)]",
  },
  learning: {
    badge: "border border-[rgba(17,184,164,0.18)] bg-[rgba(17,184,164,0.12)] text-[var(--pv-accent-strong)]",
    glow: "bg-[rgba(17,184,164,0.16)]",
  },
  action: {
    badge: "border border-[rgba(99,102,241,0.16)] bg-[rgba(99,102,241,0.1)] text-indigo-700",
    glow: "bg-[rgba(99,102,241,0.16)]",
  },
  streak: {
    badge: "border border-[rgba(245,158,11,0.18)] bg-[rgba(245,158,11,0.12)] text-amber-700",
    glow: "bg-[rgba(245,158,11,0.18)]",
  },
  challenge: {
    badge: "border border-[rgba(236,72,153,0.16)] bg-[rgba(236,72,153,0.1)] text-pink-700",
    glow: "bg-[rgba(236,72,153,0.16)]",
  },
};
