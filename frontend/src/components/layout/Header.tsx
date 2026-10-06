import { Grid3x3 } from "lucide-react";
import type { ReactNode } from "react";

export function Header({ children }: { children?: ReactNode }) {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-4 px-6 py-3">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-slate-900 text-teal-300">
            <Grid3x3 className="h-5 w-5" aria-hidden />
          </div>
          <div>
            <h1 className="text-base leading-tight font-semibold text-slate-900">GLCM Texture Analyzer</h1>
            <p className="text-xs text-slate-500">Moving Window Texture Analysis &amp; K-Means Clustering</p>
          </div>
        </div>
        {children}
      </div>
    </header>
  );
}
