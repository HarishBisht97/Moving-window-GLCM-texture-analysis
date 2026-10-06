import { ArrowRight } from "lucide-react";
import { useState } from "react";
import { Button } from "../components/common/Button";
import { Panel, SectionHeading } from "../components/common/Panel";
import { ParameterSummary } from "../components/parameters/ParameterSummary";
import { ClusterStatsTable } from "../components/statistics/ClusterStatsTable";
import { FeatureStatsTable } from "../components/statistics/FeatureStatsTable";
import { ExperimentTabs } from "../components/visualization/ExperimentTabs";
import { ImageViewer } from "../components/visualization/ImageViewer";
import type { AnalysisResult } from "../types/analysis";
import { FEATURE_ORDER } from "../utils/format";

const FEATURE_DESCRIPTIONS = {
  ASM: "Σ P(i,j)² — local uniformity",
  CON: "Σ (i−j)² P(i,j) — local gray-level variation",
  MEAN: "Σ i·Pₓ(i) — GLCM mean (quantized levels)",
} as const;

export function ResultsPage({ result, onCompare }: { result: AnalysisResult; onCompare: () => void }) {
  const [selected, setSelected] = useState(result.experiments[0]?.key ?? "original");
  const exp = result.experiments.find((e) => e.key === selected) ?? result.experiments[0];
  if (!exp) return null;
  const aspect = result.image.width / result.image.height;
  const textures = FEATURE_ORDER.map((f) => exp.textures.find((t) => t.feature === f)).filter(
    (t): t is NonNullable<typeof t> => t !== undefined,
  );

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900">Results</h2>
          <p className="mt-0.5 text-xs text-slate-500">
            {result.image.filename} · {result.image.width} × {result.image.height} px
          </p>
          <div className="mt-2">
            <ParameterSummary params={result.parameters} />
          </div>
        </div>
        <div className="flex items-center gap-3">
          <ExperimentTabs experiments={result.experiments} selected={exp.key} onSelect={setSelected} />
          <Button size="md" onClick={onCompare} icon={<ArrowRight className="h-4 w-4" aria-hidden />}>
            Compare all
          </Button>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_360px]">
        <ImageViewer
          src={exp.inputImageUrl}
          title={`Input image · ${exp.label}`}
          subtitle={exp.smoothingSize ? `${exp.smoothingSize}×${exp.smoothingSize} averaging filter` : "Grayscale input"}
          aspectRatio={aspect}
        />
        <ImageViewer
          src={exp.kmeansImageUrl}
          title={`K-Means clusters · ${exp.label}`}
          subtitle={`K = ${exp.clusters.length} on standardized [ASM, Contrast, Mean]`}
          aspectRatio={aspect}
          legend={exp.kmeansLegend}
          pixelated
        />
        <Panel title="K-Means results" subtitle={`Inertia (standardized space): ${exp.inertia.toFixed(1)}`}>
          <ClusterStatsTable clusters={exp.clusters} colors={exp.kmeansLegend.colors} />
        </Panel>
      </div>

      <div>
        <SectionHeading
          title="Texture features"
          description="Each pixel holds the feature value of the moving window centred on it. Colour scales are shared across the three experiments."
        />
        <div className="grid gap-5 md:grid-cols-3">
          {textures.map((t) => (
            <ImageViewer
              key={t.feature}
              src={t.imageUrl}
              title={t.title}
              subtitle={FEATURE_DESCRIPTIONS[t.feature]}
              downloadSrc={t.figureUrl ?? t.imageUrl}
              aspectRatio={aspect}
              legend={t.legend}
              footer={<FeatureStatsTable stats={t.statistics} />}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
