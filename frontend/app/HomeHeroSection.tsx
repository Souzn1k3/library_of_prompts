import type { PromptListItem } from "@/lib/types";

import { HomeActionWorkbench } from "./HomeActionWorkbench";

type HomeHeroSectionProps = {
  initialAuthenticated: boolean;
  entryPrompts: PromptListItem[];
  heroPromptBody: string | null;
  quickUseCases: string[];
};

export function HomeHeroSection({
  initialAuthenticated,
  entryPrompts,
  heroPromptBody,
  quickUseCases,
}: HomeHeroSectionProps) {
  return (
    <HomeActionWorkbench
      initialAuthenticated={initialAuthenticated}
      prompts={entryPrompts}
      heroPromptBody={heroPromptBody}
      quickUseCases={quickUseCases}
    />
  );
}
