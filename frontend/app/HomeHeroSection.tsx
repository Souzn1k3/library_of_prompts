import type { PromptListItem } from "@/lib/types";

import { HomeActionWorkbench } from "./HomeActionWorkbench";

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
  return (
    <HomeActionWorkbench
      prompts={entryPrompts}
      heroPromptBody={heroPromptBody}
      quickUseCases={quickUseCases}
    />
  );
}
