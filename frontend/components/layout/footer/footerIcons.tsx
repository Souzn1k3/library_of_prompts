"use client";

import type { ComponentPropsWithoutRef } from "react";

export function TelegramIcon(props: ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="m21.2 4.8-2.7 13.1c-.2 1-1 1.2-1.8.8l-4.2-3.1-2 1.9c-.2.2-.4.4-.8.4l.3-4.4 8.1-7.4c.4-.3-.1-.5-.6-.2l-10 6.3-4.3-1.4c-.9-.3-.9-.9.2-1.4L19.5 4c.8-.3 1.5.2 1.7.8Z" />
    </svg>
  );
}

export function InstagramIcon(props: ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <rect x="3.75" y="3.75" width="16.5" height="16.5" rx="4.25" />
      <circle cx="12" cy="12" r="3.75" />
      <circle cx="17.15" cy="6.85" r="0.9" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function TikTokIcon(props: ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M14 4.25c.5 1.6 1.6 2.9 3 3.7 1 .6 2 .9 3 .9" />
      <path d="M14 4.25v10.6a4.35 4.35 0 1 1-4.35-4.35c.55 0 1.07.1 1.55.29" />
    </svg>
  );
}

export function YouTubeIcon(props: ComponentPropsWithoutRef<"svg">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" {...props}>
      <path d="M20.5 7.6c-.2-1-.9-1.8-1.9-2C16.9 5.2 14.5 5 12 5S7.1 5.2 5.4 5.6c-1 .2-1.7 1-1.9 2C3.2 9.1 3 10.5 3 12s.2 2.9.5 4.4c.2 1 .9 1.8 1.9 2 1.7.4 4.1.6 6.6.6s4.9-.2 6.6-.6c1-.2 1.7-1 1.9-2 .3-1.5.5-2.9.5-4.4s-.2-2.9-.5-4.4Z" />
      <path d="m10 9.5 5 2.5-5 2.5V9.5Z" fill="currentColor" stroke="none" />
    </svg>
  );
}
