import type { ColorLegend as ColorLegendData } from "../../types/analysis";
import { fmt } from "../../utils/format";

export function ColorLegend({ legend, compact = false }: { legend: ColorLegendData; compact?: boolean }) {
  if (legend.kind === "categorical") {
    return (
      <ul className="flex flex-wrap gap-x-3 gap-y-1" aria-label="Cluster colours">
        {legend.colors.map((c, i) => (
          <li key={c} className="flex items-center gap-1.5 text-[11px] text-slate-600">
            <span className="h-2.5 w-2.5 rounded-sm border border-black/10" style={{ backgroundColor: c }} aria-hidden />
            {legend.labels?.[i] ?? `Cluster ${i}`}
          </li>
        ))}
      </ul>
    );
  }
  const gradient = `linear-gradient(to right, ${legend.colors.join(", ")})`;
  const vmin = legend.vmin ?? 0;
  const vmax = legend.vmax ?? 1;
  return (
    <div aria-label={`Colour scale from ${fmt(vmin, 3)} to ${fmt(vmax, 3)}`}>
      <div className={`${compact ? "h-1.5" : "h-2"} w-full rounded-sm border border-black/10`} style={{ background: gradient }} />
      <div className="num mt-0.5 flex justify-between text-[10px] text-slate-500">
        <span>{fmt(vmin, 3)}</span>
        {!compact && <span>{fmt((vmin + vmax) / 2, 3)}</span>}
        <span>
          {legend.clippedMax ? "≥ " : ""}
          {fmt(vmax, 3)}
        </span>
      </div>
    </div>
  );
}
