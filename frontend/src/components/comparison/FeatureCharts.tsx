import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AnalysisResult, FeatureKey } from "../../types/analysis";
import { FEATURE_LABELS, FEATURE_ORDER, fmt } from "../../utils/format";

const CASE_COLORS = ["#334155", "#0d9488", "#d97706"];

interface ChartRow {
  stat: string;
  [caseLabel: string]: number | string;
}

function rowsFor(result: AnalysisResult, feature: FeatureKey): ChartRow[] {
  const stats = result.featureStatistics.filter((r) => r.feature === feature);
  return [
    { stat: "Mean", ...Object.fromEntries(stats.map((s) => [s.case, s.mean])) },
    { stat: "Std Dev", ...Object.fromEntries(stats.map((s) => [s.case, s.std])) },
  ];
}

/** One small chart per feature (each with its own y scale): mean and std for every case. */
export function FeatureCharts({ result }: { result: AnalysisResult }) {
  const cases = result.experiments.map((e) => e.label);
  return (
    <div className="grid gap-4 lg:grid-cols-3">
      {FEATURE_ORDER.map((f) => (
        <figure key={f} className="rounded-md border border-slate-200 bg-white p-3">
          <figcaption className="mb-2 text-xs font-semibold text-slate-900">{FEATURE_LABELS[f]}: mean and standard deviation</figcaption>
          <div className="h-56" role="img" aria-label={`${FEATURE_LABELS[f]} mean and standard deviation per case`}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rowsFor(result, f)} margin={{ top: 4, right: 4, bottom: 0, left: -8 }} barCategoryGap="22%">
                <CartesianGrid strokeDasharray="2 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="stat" tick={{ fontSize: 11, fill: "#475569" }} axisLine={{ stroke: "#cbd5e1" }} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#64748b" }} axisLine={false} tickLine={false} tickFormatter={(v: number) => fmt(v, 2)} width={44} />
                <Tooltip
                  cursor={{ fill: "#f1f5f9" }}
                  formatter={(v) => (typeof v === "number" ? fmt(v) : String(v))}
                  contentStyle={{ fontSize: 11, borderRadius: 6, borderColor: "#cbd5e1" }}
                />
                <Legend
                  wrapperStyle={{ fontSize: 11 }}
                  iconType="square"
                  iconSize={8}
                  itemSorter={(item) => cases.indexOf(String(item.dataKey))}
                />
                {cases.map((c, i) => (
                  <Bar key={c} dataKey={c} fill={CASE_COLORS[i % CASE_COLORS.length]} radius={[2, 2, 0, 0]} isAnimationActive={false} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </figure>
      ))}
    </div>
  );
}
