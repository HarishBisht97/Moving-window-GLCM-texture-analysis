import { Check, Circle, Loader2, X } from "lucide-react";
import type { JobStatus, StageState } from "../../types/analysis";

function StageIcon({ state }: { state: StageState }) {
  switch (state) {
    case "done":
      return <Check className="h-3.5 w-3.5 text-teal-700" aria-hidden />;
    case "active":
      return <Loader2 className="h-3.5 w-3.5 animate-spin text-teal-700" aria-hidden />;
    case "failed":
      return <X className="h-3.5 w-3.5 text-red-600" aria-hidden />;
    default:
      return <Circle className="h-3 w-3 text-slate-300" aria-hidden />;
  }
}

const STATE_TEXT: Record<StageState, string> = { done: "done", active: "in progress", failed: "failed", pending: "pending" };

export function ProcessingStages({ status }: { status: JobStatus | undefined }) {
  if (!status) {
    return (
      <div className="flex items-center gap-2 py-6 text-sm text-slate-600">
        <Loader2 className="h-4 w-4 animate-spin text-teal-700" aria-hidden /> Starting analysis…
      </div>
    );
  }
  const heading =
    status.state === "queued"
      ? "Queued"
      : status.state === "failed"
        ? "Analysis failed"
        : status.state === "completed"
          ? "Complete"
          : "Processing image";

  return (
    <div>
      <div className="mb-3 flex items-baseline justify-between">
        <p className="text-sm font-semibold text-slate-900">{heading}</p>
        {status.elapsedSeconds !== null && (
          <p className="num text-xs text-slate-500">{status.elapsedSeconds.toFixed(1)} s</p>
        )}
      </div>
      <ol className="flex flex-col gap-0.5" aria-live="polite">
        {status.stages.map((s) => (
          <li
            key={s.id}
            className={`flex items-center gap-2.5 rounded px-2 py-1 text-xs ${
              s.state === "active" ? "bg-teal-50 font-medium text-teal-900" : s.state === "pending" ? "text-slate-400" : "text-slate-700"
            }`}
          >
            <span className="flex h-4 w-4 shrink-0 items-center justify-center">
              <StageIcon state={s.state} />
            </span>
            <span>{s.label}</span>
            <span className="sr-only">({STATE_TEXT[s.state]})</span>
          </li>
        ))}
        <li className={`flex items-center gap-2.5 px-2 py-1 text-xs ${status.state === "completed" ? "font-medium text-teal-800" : "text-slate-400"}`}>
          <span className="flex h-4 w-4 items-center justify-center">
            <StageIcon state={status.state === "completed" ? "done" : "pending"} />
          </span>
          Complete
        </li>
      </ol>
      <p className="mt-3 text-[11px] text-slate-500">Stage updates are reported by the backend as each pipeline step starts.</p>
    </div>
  );
}
