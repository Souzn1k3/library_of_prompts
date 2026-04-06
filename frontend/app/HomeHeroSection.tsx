import type { PromptListItem } from "@/lib/types";

import { HomeWorkbenchRuntime } from "./HomeWorkbenchRuntime";

type HomeHeroSectionProps = {
  entryPrompts: PromptListItem[];
  heroPromptBody: string | null;
  quickUseCases: string[];
};

export function HomeHeroSection({
  entryPrompts,
  heroPromptBody,
  quickUseCases,
}: HomeHeroSectionProps) {
  void heroPromptBody;
  void quickUseCases;
  return <HomeWorkbenchRuntime prompts={entryPrompts} />;
}
