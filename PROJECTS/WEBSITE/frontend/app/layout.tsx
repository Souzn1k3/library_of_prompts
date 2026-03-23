import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { LanguageProvider } from "@/components/i18n/LanguageProvider";
import { T } from "@/components/i18n/T";
import { OnboardingBanner } from "@/components/OnboardingBanner";
import { Footer } from "@/components/layout/Footer";
import { Header } from "@/components/layout/Header";
import { OrganizationJsonLd, WebSiteJsonLd } from "@/components/seo/JsonLd";
import { getSiteUrl } from "@/lib/site";

import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

const siteUrl = getSiteUrl();

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Prompts Vault",
    template: "%s · Prompts Vault",
  },
  description:
    "Structured prompts, prompt engineering education, and a searchable library for students, developers, and practitioners.",
  applicationName: "Prompts Vault",
  keywords: [
    "prompt engineering",
    "AI prompts",
    "ChatGPT prompts",
    "few-shot prompting",
    "chain of thought",
    "zero-shot",
    "prompt library",
  ],
  authors: [{ name: "Prompts Vault" }],
  openGraph: {
    type: "website",
    locale: "en_US",
    url: siteUrl,
    siteName: "Prompts Vault",
    title: "Prompts Vault",
    description:
      "Structured prompts, prompt engineering education, and a searchable library.",
  },
  twitter: {
    card: "summary_large_image",
    title: "Prompts Vault",
    description:
      "Structured prompts, prompt engineering education, and a searchable library.",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
    },
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.className} flex min-h-screen flex-col bg-white text-zinc-900 antialiased`}
      >
        <LanguageProvider>
          <a href="#main-content" className="skip-link">
            <T k="a11y.skipToContent" />
          </a>
          <OrganizationJsonLd />
          <WebSiteJsonLd />
          <OnboardingBanner />
          <Header />
          <main
            id="main-content"
            className="mx-auto w-full max-w-5xl flex-1 px-4 py-10"
            tabIndex={-1}
          >
            {children}
          </main>
          <Footer />
        </LanguageProvider>
      </body>
    </html>
  );
}
