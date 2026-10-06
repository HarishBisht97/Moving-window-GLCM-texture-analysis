import type { ReactNode } from "react";

interface PanelProps {
  title?: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}

export function Panel({ title, subtitle, actions, children, className = "", bodyClassName = "p-4" }: PanelProps) {
  return (
    <section className={`rounded-md border border-slate-200 bg-white ${className}`}>
      {(title || actions) && (
        <header className="flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-2.5">
          <div className="min-w-0">
            {title && <h2 className="text-sm font-semibold text-slate-900">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={bodyClassName}>{children}</div>
    </section>
  );
}

export function SectionHeading({ title, description }: { title: string; description?: string }) {
  return (
    <div className="mb-3">
      <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      {description && <p className="mt-0.5 text-xs text-slate-500">{description}</p>}
    </div>
  );
}
