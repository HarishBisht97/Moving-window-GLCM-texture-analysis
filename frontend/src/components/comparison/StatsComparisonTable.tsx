import type { FeatureStatisticsRow } from "../../types/analysis";
import { FEATURE_LABELS, fmt } from "../../utils/format";

const th = "px-3 py-2 text-left text-[11px] font-medium tracking-wide text-slate-500 uppercase";
const td = "num px-3 py-1.5 text-right text-slate-900";

export function StatsComparisonTable({ rows }: { rows: FeatureStatisticsRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <thead className="border-b border-slate-200 bg-slate-50">
          <tr>
            <th className={th}>Case</th>
            <th className={th}>Feature</th>
            <th className={`${th} text-right`}>Min</th>
            <th className={`${th} text-right`}>Max</th>
            <th className={`${th} text-right`}>Mean</th>
            <th className={`${th} text-right`}>Std</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => {
            const firstOfCase = i === 0 || rows[i - 1]?.case !== r.case;
            return (
              <tr key={`${r.case}-${r.feature}`} className={firstOfCase && i > 0 ? "border-t border-slate-300" : "border-t border-slate-100"}>
                <td className="px-3 py-1.5 font-medium text-slate-800">{firstOfCase ? r.case : ""}</td>
                <td className="px-3 py-1.5 text-slate-700">{FEATURE_LABELS[r.feature]}</td>
                <td className={td}>{fmt(r.min)}</td>
                <td className={td}>{fmt(r.max)}</td>
                <td className={td}>{fmt(r.mean)}</td>
                <td className={td}>{fmt(r.std)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
