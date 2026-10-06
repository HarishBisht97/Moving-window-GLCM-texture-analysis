import type { TextureStatistics } from "../../types/analysis";
import { fmt } from "../../utils/format";

export function FeatureStatsTable({ stats }: { stats: TextureStatistics }) {
  const rows: [string, number][] = [
    ["Min", stats.min],
    ["Max", stats.max],
    ["Mean", stats.mean],
    ["Std Dev", stats.std],
  ];
  return (
    <dl className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs">
      {rows.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-2">
          <dt className="text-slate-500">{k}</dt>
          <dd className="num text-slate-900">{fmt(v)}</dd>
        </div>
      ))}
    </dl>
  );
}
