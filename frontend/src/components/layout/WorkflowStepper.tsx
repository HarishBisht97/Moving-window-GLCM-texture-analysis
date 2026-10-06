import { Check } from "lucide-react";

export type StepId = "upload" | "configure" | "run" | "results" | "compare";

export const STEPS: { id: StepId; label: string }[] = [
  { id: "upload", label: "Upload Image" },
  { id: "configure", label: "Configure" },
  { id: "run", label: "Run Analysis" },
  { id: "results", label: "Results" },
  { id: "compare", label: "Compare" },
];

interface WorkflowStepperProps {
  current: StepId;
  completed: Set<StepId>;
  enabled: Set<StepId>;
  onSelect: (step: StepId) => void;
}

export function WorkflowStepper({ current, completed, enabled, onSelect }: WorkflowStepperProps) {
  return (
    <nav aria-label="Workflow" className="border-b border-slate-200 bg-white">
      <ol className="mx-auto flex max-w-[1440px] items-center gap-1 overflow-x-auto px-6 py-2">
        {STEPS.map((step, i) => {
          const isCurrent = step.id === current;
          const isDone = completed.has(step.id) && !isCurrent;
          const isEnabled = enabled.has(step.id);
          return (
            <li key={step.id} className="flex items-center">
              {i > 0 && <span className={`mx-1 h-px w-6 sm:w-10 ${isDone || isCurrent ? "bg-teal-600" : "bg-slate-200"}`} aria-hidden />}
              <button
                type="button"
                disabled={!isEnabled}
                aria-current={isCurrent ? "step" : undefined}
                onClick={() => onSelect(step.id)}
                className={`flex items-center gap-2 rounded-md px-2 py-1.5 text-xs whitespace-nowrap transition-colors disabled:cursor-not-allowed ${
                  isCurrent
                    ? "bg-teal-50 font-semibold text-teal-800"
                    : isEnabled
                      ? "text-slate-700 hover:bg-slate-100"
                      : "text-slate-400"
                }`}
              >
                <span
                  className={`flex h-5 w-5 items-center justify-center rounded-full border text-[10px] font-semibold ${
                    isCurrent
                      ? "border-teal-700 bg-teal-700 text-white"
                      : isDone
                        ? "border-teal-600 bg-white text-teal-700"
                        : "border-slate-300 bg-white text-slate-400"
                  }`}
                >
                  {isDone ? <Check className="h-3 w-3" aria-hidden /> : i + 1}
                </span>
                {step.label}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
