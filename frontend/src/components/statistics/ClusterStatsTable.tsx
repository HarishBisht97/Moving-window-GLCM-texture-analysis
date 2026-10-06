import type { ClusterStatistics } from "../../types/analysis";
import { fmt, fmtInt, fmtPercent } from "../../utils/format";

interface ClusterStatsTableProps {
  clusters: ClusterStatistics[];
  colors: string[];
}

const th = "px-2 py-1.5 text-left text-[11px] font-medium text-slate-500";
const td = "num px-2 py-1 text-right text-slate-900";

export function ClusterStatsTable({ clusters, colors }: ClusterStatsTableProps) {
  return (
    <div className="flex flex-col gap-4">
      <div>
        <p className="label-caps mb-1.5">Cluster sizes</p>
        <table className="w-full text-xs">
          <thead className="border-b border-slate-200">
            <tr>
              <th className={th}>Cluster</th>
              <th className={`${th} text-right`}>Pixels</th>
              <th className={`${th} text-right`}>Percentage</th>
              <th className={`${th} w-1/3`}>
                <span className="sr-only">Share bar</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {clusters.map((c) => (
              <tr key={c.cluster}>
                <td className="px-2 py-1">
                  <span className="flex items-center gap-1.5 text-slate-800">
                    <span className="h-2.5 w-2.5 rounded-sm border border-black/10" style={{ backgroundColor: colors[c.cluster] }} aria-hidden />
                    {c.cluster}
                  </span>
                </td>
                <td className={td}>{fmtInt(c.pixels)}</td>
                <td className={td}>{fmtPercent(c.percent)}</td>
                <td className="px-2 py-1">
                  <div className="h-1.5 w-full rounded-sm bg-slate-100" aria-hidden>
                    <div className="h-1.5 rounded-sm" style={{ width: `${c.percent}%`, backgroundColor: colors[c.cluster] }} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div>
        <p className="label-caps mb-1.5">Cluster centres (feature units)</p>
        <table className="w-full text-xs">
          <thead className="border-b border-slate-200">
            <tr>
              <th className={th}>Cluster</th>
              <th className={`${th} text-right`}>ASM</th>
              <th className={`${th} text-right`}>Contrast</th>
              <th className={`${th} text-right`}>Mean</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {clusters.map((c) => (
              <tr key={c.cluster}>
                <td className="px-2 py-1">
                  <span className="flex items-center gap-1.5 text-slate-800">
                    <span className="h-2.5 w-2.5 rounded-sm border border-black/10" style={{ backgroundColor: colors[c.cluster] }} aria-hidden />
                    {c.cluster}
                  </span>
                </td>
                <td className={td}>{fmt(c.centerAsm)}</td>
                <td className={td}>{fmt(c.centerCon)}</td>
                <td className={td}>{fmt(c.centerMean)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="mt-1.5 text-[11px] text-slate-500">
          Clusters are numbered by increasing Mean centre, so the same ID has a comparable brightness rank in every experiment.
        </p>
      </div>

      <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] text-amber-900">
        Cluster IDs represent texture groups produced by K-Means and are not automatically land-cover classes.
      </p>
    </div>
  );
}
