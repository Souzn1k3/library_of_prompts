import { getSiteUrl } from "@/lib/site";

type JsonLdProps = {
  id: string;
  data: Record<string, unknown>;
};

function serializeJsonLd(data: Record<string, unknown>): string {
  return JSON.stringify(data)
    .replace(/</g, "\\u003c")
    .replace(/>/g, "\\u003e")
    .replace(/&/g, "\\u0026")
    .replace(/\u2028/g, "\\u2028")
    .replace(/\u2029/g, "\\u2029");
}

export function JsonLd({ id, data }: JsonLdProps) {
  return (
    <script
      id={id}
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: serializeJsonLd(data) }}
    />
  );
}

export function OrganizationJsonLd() {
  const url = getSiteUrl();
  return (
    <JsonLd
      id="ld-org"
      data={{
        "@context": "https://schema.org",
        "@type": "Organization",
        name: "Prompts Vault",
        url,
        description:
          "Structured prompts, prompt engineering education, and a searchable library.",
      }}
    />
  );
}

export function WebSiteJsonLd() {
  const url = getSiteUrl();
  return (
    <JsonLd
      id="ld-website"
      data={{
        "@context": "https://schema.org",
        "@type": "WebSite",
        name: "Prompts Vault",
        url,
        potentialAction: {
          "@type": "SearchAction",
          target: {
            "@type": "EntryPoint",
            urlTemplate: `${url}/catalog?q={search_term_string}`,
          },
          "query-input": "required name=search_term_string",
        },
      }}
    />
  );
}
