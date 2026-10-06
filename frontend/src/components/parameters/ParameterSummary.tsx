import type { AnalysisParameters } from "../../types/analysis";

export function ParameterSummary({ params }: { params: AnalysisParameters }) {
  const items: [string, string][] = [
    ["Window", `${params.glcmWindowSize}×${params.glcmWindowSize}`],
    ["Levels", String(params.grayLevels)],
    ["d", String(params.distance)],
    ["θ", `${params.angle}°`],
    ["K", String(params.clusters)],
    ["Seed", String(params.randomState)],
  ];
  return (
    <ul className="flex flex-wrap gap-1.5" aria-label="Analysis parameters">
      {items.map(([k, v]) => (
        <li key={k} className="rounded border border-slate-200 bg-white px-1.5 py-0.5 text-[11px] text-slate-500">
          {k} <span className="num font-medium text-slate-900">{v}</span>
        </li>
      ))}
    </ul>
  );
}
