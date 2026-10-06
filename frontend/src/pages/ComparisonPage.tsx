import { ComparisonGrid } from "../components/comparison/ComparisonGrid";
import { DownloadPanel } from "../components/comparison/DownloadPanel";
import { FeatureCharts } from "../components/comparison/FeatureCharts";
import { SmoothingEffect } from "../components/comparison/SmoothingEffect";
import { SmoothingRow } from "../components/comparison/SmoothingRow";
import { StatsComparisonTable } from "../components/comparison/StatsComparisonTable";
import { Panel } from "../components/common/Panel";
import { ParameterSummary } from "../components/parameters/ParameterSummary";
import type { AnalysisResult } from "../types/analysis";

const SECTIONS = [
  ["grid", "Comparison grid"],
  ["smoothing", "Smoothing"],
  ["statistics", "Statistics"],
  ["charts", "Charts"],
  ["effect", "Effect of smoothing"],
  ["downloads", "Downloads"],
] as const;

export function ComparisonPage({ result }: { result: AnalysisResult }) {
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Comparison</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            Original vs {result.smoothingSizes.map((s) => `${s}×${s}`).join(" vs ")} averaging, processed with identical GLCM and
            K-Means parameters.
          </p>
          <div className="mt-2">
            <ParameterSummary params={result.parameters} />
          </div>
        </div>
        <nav aria-label="Comparison sections" className="flex flex-wrap gap-1">
          {SECTIONS.map(([id, label]) => (
            <a key={id} href={`#${id}`} className="rounded px-2 py-1 text-xs text-slate-600 hover:bg-slate-100 hover:text-slate-900">
              {label}
            </a>
          ))}
        </nav>
      </div>

      <Panel
        title={<span id="grid" className="scroll-mt-4">Texture comparison grid</span>}
        subtitle="Rows: output type · Columns: experiment. Each row shares one colour scale, so differences in colour reflect differences in value."
      >
        <ComparisonGrid result={result} />
      </Panel>

      <Panel title={<span id="smoothing" className="scroll-mt-4">Smoothing comparison</span>} subtitle="Input images to the GLCM stage. Click an image to view it fullscreen.">
        <SmoothingRow result={result} />
      </Panel>

      <Panel title={<span id="statistics" className="scroll-mt-4">Statistical comparison</span>} subtitle="Texture-feature statistics over all pixels" bodyClassName="p-0">
        <StatsComparisonTable rows={result.featureStatistics} />
      </Panel>

      <Panel
        title={<span id="charts" className="scroll-mt-4">Feature comparison charts</span>}
        subtitle="Separate y-axes per feature because ASM, Contrast and Mean have different ranges"
      >
        <FeatureCharts result={result} />
      </Panel>

      <Panel title={<span id="effect" className="scroll-mt-4">Effect of smoothing</span>} subtitle="Raw measured changes first, interpretation below">
        <SmoothingEffect result={result} />
      </Panel>

      <Panel title={<span id="downloads" className="scroll-mt-4">Download results</span>}>
        <DownloadPanel files={result.downloads} zipUrl={result.zipUrl} />
      </Panel>
    </div>
  );
}
