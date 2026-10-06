import { Info } from "lucide-react";
import { useId, type ReactNode } from "react";

/** Info icon with an accessible hover / focus tooltip. */
export function InfoTooltip({ children }: { children: ReactNode }) {
  const id = useId();
  return (
    <span className="group relative inline-flex">
      <button
        type="button"
        aria-describedby={id}
        className="inline-flex h-4 w-4 items-center justify-center rounded-full text-slate-400 hover:text-slate-700"
      >
        <Info className="h-3.5 w-3.5" aria-hidden />
        <span className="sr-only">More information</span>
      </button>
      <span
        id={id}
        role="tooltip"
        className="pointer-events-none invisible absolute bottom-full left-1/2 z-30 mb-2 w-64 -translate-x-1/2 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs leading-relaxed font-normal text-slate-100 opacity-0 transition-opacity group-focus-within:visible group-focus-within:opacity-100 group-hover:visible group-hover:opacity-100"
      >
        {children}
      </span>
    </span>
  );
}
