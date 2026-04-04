const OFFICIAL_TEAM_CONTRIBUTOR_SLUGS = new Set(["prompts-vault-curated"]);

function normalize(value: string | null | undefined): string {
  return (value ?? "").trim().toLowerCase();
}

export function isOfficialTeamContributor(
  contributorSlug?: string | null,
): boolean {
  const normalizedSlug = normalize(contributorSlug);
  return normalizedSlug.length > 0 && OFFICIAL_TEAM_CONTRIBUTOR_SLUGS.has(normalizedSlug);
}
