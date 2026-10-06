import type { ExperimentResult } from "../../types/analysis";

interface ExperimentTabsProps {
  experiments: ExperimentResult[];
  selected: string;
  onSelect: (key: string) => void;
}

export function ExperimentTabs({ experiments, selected, onSelect }: ExperimentTabsProps) {
  return (
    <div role="tablist" aria-label="Experiment" className="inline-flex rounded-md border border-slate-300 bg-white p-0.5">
      {experiments.map((e) => {
        const active = e.key === selected;
        return (
          <button
            key={e.key}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onSelect(e.key)}
            className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${
              active ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
            }`}
          >
            {e.smoothingSize ? `${e.smoothingSize}×${e.smoothingSize} Smoothed` : "Original"}
          </button>
        );
      })}
    </div>
  );
}
