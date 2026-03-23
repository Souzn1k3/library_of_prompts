export function PageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded bg-zinc-200" />
      <div className="h-4 w-full max-w-2xl animate-pulse rounded bg-zinc-100" />
      <div className="h-4 w-full max-w-xl animate-pulse rounded bg-zinc-100" />
      <div className="grid gap-4 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-48 animate-pulse rounded-lg border border-zinc-100 bg-zinc-50" />
        ))}
      </div>
    </div>
  );
}
