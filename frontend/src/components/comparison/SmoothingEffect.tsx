import type { AnalysisResult, FeatureKey, FeatureStatisticsRow, MetricsRow } from "../../types/analysis";
import { FEATURE_LABELS, FEATURE_ORDER, fmt, fmtChange, percentChange, shortCase } from "../../utils/format";
import { MarkdownText } from "./MarkdownText";

function ChangeBadge({ change }: { change: number | null }) {
  if (change === null) return <span className="text-slate-400">n/a</span>;
  const tone = Math.abs(change) < 0.5 ? "text-slate-500" : change > 0 ? "text-teal-700" : "text-rose-700";
  return <span className={`num ${tone}`}>{fmtChange(change)}</span>;
}

/** Wording derived from the sign of the measured change, never assumed. */
function direction(change: number | null): string {
  if (change === null) return "could not be compared";
  if (Math.abs(change) < 0.5) return "stayed practically unchanged";
  return change > 0 ? "increased" : "decreased";
}

const METRICS: { key: string; label: string; digits: number }[] = [
  { key: "High-freq energy", label: "High-frequency energy of the input", digits: 2 },
  { key: "Uniform windows (ASM=1) %", label: "Uniform windows (ASM = 1), %", digits: 2 },
  { key: "Zero-contrast windows %", label: "Zero-contrast windows, %", digits: 2 },
  { key: "Distinct [ASM,CON,MEAN] vectors", label: "Distinct [ASM, CON, MEAN] vectors", digits: 0 },
  { key: "Cluster boundary pixels %", label: "Cluster-boundary pixels, %", digits: 2 },
  { key: "Effective no. of clusters", label: "Effective number of clusters", digits: 2 },
  { key: "ARI vs original", label: "Adjusted Rand Index vs original", digits: 3 },
];

export function SmoothingEffect({ result }: { result: AnalysisResult }) {
  const exps = result.experiments;
  const byCase = (feature: FeatureKey) =>
    exps.map((e) => result.featureStatistics.find((r) => r.case === e.label && r.feature === feature));
  const metricsByCase = exps.map((e) => result.metrics.find((m: MetricsRow) => m.Case === e.label));

  return (
    <div className="flex flex-col gap-5">
      <div>
        <p className="label-caps mb-2">Observed changes in texture statistics</p>
        <div className="grid gap-3 lg:grid-cols-3">
          {FEATURE_ORDER.map((f) => {
            const rows = byCase(f);
            const base = rows[0];
            return (
              <div key={f} className="rounded-md border border-slate-200 bg-white">
                <p className="border-b border-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-900">{FEATURE_LABELS[f]}</p>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="text-[11px] text-slate-500">
                      <th className="px-3 py-1 text-left font-medium">Case</th>
                      <th className="px-2 py-1 text-right font-medium">Mean</th>
                      <th className="px-2 py-1 text-right font-medium">Δ</th>
                      <th className="px-2 py-1 text-right font-medium">Std</th>
                      <th className="px-3 py-1 text-right font-medium">Δ</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {rows.map((r: FeatureStatisticsRow | undefined, i) => {
                      const e = exps[i];
                      if (!r || !e) return null;
                      return (
                        <tr key={r.case}>
                          <td className="px-3 py-1 text-slate-700">{shortCase(e.label, e.smoothingSize)}</td>
                          <td className="num px-2 py-1 text-right text-slate-900">{fmt(r.mean)}</td>
                          <td className="px-2 py-1 text-right">{i === 0 || !base ? "—" : <ChangeBadge change={percentChange(base.mean, r.mean)} />}</td>
                          <td className="num px-2 py-1 text-right text-slate-900">{fmt(r.std)}</td>
                          <td className="px-3 py-1 text-right">{i === 0 || !base ? "—" : <ChangeBadge change={percentChange(base.std, r.std)} />}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                {base && (
                  <p className="border-t border-slate-100 px-3 py-1.5 text-[11px] leading-relaxed text-slate-600">
                    {rows.slice(1).map((r, j) => {
                      const e = exps[j + 1];
                      if (!r || !e) return null;
                      const c = percentChange(base.mean, r.mean);
                      return (
                        <span key={r.case} className="block">
                          With {shortCase(e.label, e.smoothingSize)} averaging, mean {FEATURE_LABELS[f]} {direction(c)} ({fmtChange(c)}).
                        </span>
                      );
                    })}
                  </p>
                )}
              </div>
            );
          })}
        </div>
        <p className="mt-1.5 text-[11px] text-slate-500">Δ = percentage change relative to the original image, computed from the backend statistics.</p>
      </div>

      <div>
        <p className="label-caps mb-2">Image and clustering metrics</p>
        <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
          <table className="w-full text-xs">
            <thead className="border-b border-slate-200 bg-slate-50">
              <tr>
                <th className="px-3 py-1.5 text-left text-[11px] font-medium text-slate-500">Metric</th>
                {exps.map((e) => (
                  <th key={e.key} className="px-3 py-1.5 text-right text-[11px] font-medium text-slate-500">
                    {shortCase(e.label, e.smoothingSize)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {METRICS.filter((m) => metricsByCase.every((row) => row && typeof row[m.key] === "number")).map((m) => (
                <tr key={m.key}>
                  <td className="px-3 py-1 text-slate-700">{m.label}</td>
                  {metricsByCase.map((row, i) => (
                    <td key={exps[i]?.key ?? i} className="num px-3 py-1 text-right text-slate-900">
                      {m.digits === 0 ? Number(row?.[m.key]).toLocaleString("en-US") : fmt(Number(row?.[m.key]), m.digits)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {result.interpretation && (
        <div className="rounded-md border border-slate-200 bg-white p-4">
          <p className="label-caps">Interpretation</p>
          <p className="mt-0.5 mb-2 text-[11px] text-slate-500">
            Generated by the backend from the statistics above; each increase or decrease statement follows the measured values.
          </p>
          <MarkdownText source={result.interpretation} />
        </div>
      )}
    </div>
  );
}
