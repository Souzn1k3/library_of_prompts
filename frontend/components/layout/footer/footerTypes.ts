import type { ComponentPropsWithoutRef, ReactNode } from "react";

export type FooterLink = {
  href: string;
  label: string;
  external?: boolean;
};

export type FooterSection = {
  id: string;
  title: string;
  links: FooterLink[];
};

export type SocialLink = {
  id: string;
  href: string;
  label: string;
  icon: (props: ComponentPropsWithoutRef<"svg">) => ReactNode;
};
