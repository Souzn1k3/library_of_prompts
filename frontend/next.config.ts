import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: "standalone",
  async rewrites() {
    const apiOrigin = (process.env.API_URL ?? "http://localhost:8000").replace(/\/$/, "");
    return [
      {
        source: "/api-proxy/:path*",
        destination: `${apiOrigin}/:path*`,
      },
    ];
  },
  async redirects() {
    return [
      {
        source: "/collections",
        destination: "/catalog",
        permanent: true,
      },
      {
        source: "/collections/best-prompts-for-students",
        destination: "/catalog?q=study%20summary%20exam%20explain%20concept&sort=most_saved",
        permanent: true,
      },
      {
        source: "/collections/debugging-prompts-for-react",
        destination: "/catalog?q=react%20debugging%20bug%20fix%20stack%20trace&use_case=debugging&tag=react&output_type=code&sort=most_used",
        permanent: true,
      },
      {
        source: "/collections/productivity-prompts-for-developers",
        destination: "/catalog?q=developer%20productivity%20planning%20refactor%20checklist&output_type=code&sort=trending",
        permanent: true,
      },
      {
        source: "/collections/beginner-ai-prompts",
        destination: "/catalog?difficulty=beginner&sort=most_saved",
        permanent: true,
      },
      {
        source: "/collections/structured-output-prompts",
        destination: "/catalog?output_type=structured&sort=most_used",
        permanent: true,
      },
      {
        source: "/collections/:slug",
        destination: "/catalog",
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
