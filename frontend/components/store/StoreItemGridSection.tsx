"use client";

import { StoreItemCard } from "@/components/store/StoreItemCard";
import type { StoreItem } from "@/lib/types";

type StoreItemGridSectionProps = {
  title: string;
  items: StoreItem[];
  purchasing: string | null;
  onPurchase: (item: StoreItem) => Promise<void>;
  locale: string;
  kicker?: string;
  body?: string;
  gridClassName?: string;
  keyPrefix?: string;
};

export function StoreItemGridSection({
  title,
  items,
  purchasing,
  onPurchase,
  locale,
  kicker,
  body,
  gridClassName,
  keyPrefix,
}: StoreItemGridSectionProps) {
  const resolvedGridClassName = gridClassName ?? (items.length > 1 ? "md:grid-cols-2" : "");

  return (
    <section className="space-y-3">
      <div className="pv-section-head">
        <div className="pv-section-copy">
          {kicker ? <p className="pv-kicker">{kicker}</p> : null}
          <h2 className="mt-2 text-2xl font-bold tracking-[-0.04em] text-zinc-950">{title}</h2>
          {body ? <p className="mt-2 max-w-2xl text-sm text-zinc-600">{body}</p> : null}
        </div>
      </div>

      <div className={`grid gap-4 ${resolvedGridClassName}`}>
        {items.map((item) => (
          <StoreItemCard
            key={`${keyPrefix ?? "item"}-${item.id}`}
            item={item}
            purchasing={purchasing}
            onPurchase={onPurchase}
            locale={locale}
          />
        ))}
      </div>
    </section>
  );
}
