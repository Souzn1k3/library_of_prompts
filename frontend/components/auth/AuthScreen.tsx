import type { ReactNode } from "react";

type AuthScreenItem = {
  title: ReactNode;
  body: ReactNode;
};

type AuthScreenProps = {
  eyebrow: ReactNode;
  title: ReactNode;
  subtitle: ReactNode;
  items: AuthScreenItem[];
  actions?: ReactNode;
  form: ReactNode;
};

export function AuthScreen({
  eyebrow,
  title,
  subtitle,
  items,
  actions,
  form,
}: AuthScreenProps) {
  return (
    <div className="pv-auth-shell">
      <section className="pv-auth-aside">
        <div className="space-y-4">
          <p className="pv-kicker">{eyebrow}</p>
          <h1 className="pv-auth-title">{title}</h1>
          <p className="pv-lead max-w-[34rem]">{subtitle}</p>
        </div>

        <div className="pv-auth-value-list">
          {items.map((item, index) => (
            <article key={`auth-item-${index}`} className="pv-auth-value-item">
              <p className="text-base font-semibold tracking-[-0.03em] text-zinc-950">{item.title}</p>
              <p className="mt-2 text-sm leading-relaxed text-zinc-600">{item.body}</p>
            </article>
          ))}
        </div>

        {actions ? <div className="pv-auth-actions">{actions}</div> : null}
      </section>

      <section className="pv-auth-form-panel">{form}</section>
    </div>
  );
}
