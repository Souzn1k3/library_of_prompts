import type { PromptListItem } from "@/lib/types";
import type { TranslationKey } from "@/lib/i18n";

type UnfinishedItem = {
  slug: string;
  task: string;
  updatedAt: string;
};

type HomeWorkbenchContinuityBlocksProps = {
  t: (key: TranslationKey, params?: Record<string, string | number | null | undefined>) => string;
  unfinished: UnfinishedItem[];
  recentSlugs: string[];
  promptBySlug: Map<string, PromptListItem>;
  onResume: (slug: string, task: string) => void;
  onSelectRecent: (slug: string) => void;
};

export function HomeWorkbenchContinuityBlocks({
  t,
  unfinished,
  recentSlugs,
  promptBySlug,
  onResume,
  onSelectRecent,
}: HomeWorkbenchContinuityBlocksProps) {
  return (
    <>
      {unfinished.length ? (
        <div className="space-y-2 rounded-[1rem] border border-zinc-200 bg-zinc-50/70 p-3">
          <p className="text-sm font-semibold text-zinc-900">{t("home.entryUnfinishedTitle")}</p>
          <div className="space-y-2">
            {unfinished.map((item) => {
              const prompt = promptBySlug.get(item.slug);
              if (!prompt) {
                return null;
              }

              return (
                <div key={`unfinished-${item.slug}`} className="rounded-[0.8rem] border border-zinc-200 bg-white p-2.5">
                  <p className="text-xs font-semibold text-zinc-900">{prompt.title}</p>
                  <p className="mt-1 line-clamp-2 text-xs text-zinc-600">{item.task}</p>
                  <button
                    type="button"
                    onClick={() => onResume(item.slug, item.task)}
                    className="mt-2 text-xs font-semibold text-[var(--pv-brand-strong)]"
                  >
                    {t("home.entryUnfinishedResume")}
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      ) : null}

      {recentSlugs.length ? (
        <div className="space-y-2 rounded-[1rem] border border-zinc-200 bg-zinc-50/70 p-3">
          <p className="text-sm font-semibold text-zinc-900">{t("home.entryRecentTitle")}</p>
          <div className="flex flex-wrap gap-2">
            {recentSlugs.slice(0, 5).map((slug) => {
              const prompt = promptBySlug.get(slug);
              if (!prompt) {
                return null;
              }
              return (
                <button
                  key={`recent-${slug}`}
                  type="button"
                  onClick={() => onSelectRecent(slug)}
                  className="rounded-full border border-zinc-200 bg-white px-3 py-1.5 text-xs font-semibold text-zinc-700"
                >
                  {prompt.title}
                </button>
              );
            })}
          </div>
        </div>
      ) : null}
    </>
  );
}
