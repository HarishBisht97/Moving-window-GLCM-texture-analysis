import type { AnalysisResult, ColorLegend as ColorLegendData, ExperimentResult } from "../../types/analysis";
import { FEATURE_LABELS, FEATURE_ORDER } from "../../utils/format";
import { ColorLegend } from "../visualization/ColorLegend";
import { ImageViewer } from "../visualization/ImageViewer";

interface RowSpec {
  id: string;
  label: string;
  legend?: ColorLegendData;
  tile: (e: ExperimentResult) => { src: string; download: string | null; pixelated?: boolean };
}

export function ComparisonGrid({ result }: { result: AnalysisResult }) {
  const exps = result.experiments;
  const first = exps[0];
  if (!first) return null;
  const aspect = result.image.width / result.image.height;

  const rows: RowSpec[] = [
    { id: "input", label: "Input", tile: (e) => ({ src: e.inputImageUrl, download: e.inputImageUrl }) },
    ...FEATURE_ORDER.map<RowSpec>((f) => ({
      id: f,
      label: FEATURE_LABELS[f],
      legend: first.textures.find((t) => t.feature === f)?.legend,
      tile: (e) => {
        const t = e.textures.find((x) => x.feature === f);
        return { src: t?.imageUrl ?? "", download: t?.figureUrl ?? t?.imageUrl ?? null };
      },
    })),
    {
      id: "kmeans",
      label: "K-Means",
      legend: first.kmeansLegend,
      tile: (e) => ({ src: e.kmeansImageUrl, download: e.kmeansImageUrl, pixelated: true }),
    },
  ];

  return (
    <div className="overflow-x-auto">
      <div className="grid min-w-[760px] grid-cols-[140px_repeat(3,minmax(0,1fr))] gap-3">
        <div />
        {exps.map((e) => (
          <div key={e.key} className="border-b-2 border-slate-900 pb-1 text-center text-xs font-semibold text-slate-900">
            {e.smoothingSize ? `${e.smoothingSize}×${e.smoothingSize} Smooth` : "Original"}
          </div>
        ))}
        {rows.map((row) => (
          <Row key={row.id} row={row} exps={exps} aspect={aspect} />
        ))}
      </div>
    </div>
  );
}

function Row({ row, exps, aspect }: { row: RowSpec; exps: ExperimentResult[]; aspect: number }) {
  return (
    <>
      <div className="flex flex-col justify-center gap-2 pr-1">
        <p className="text-xs font-semibold text-slate-900">{row.label}</p>
        {row.legend && <ColorLegend legend={row.legend} compact />}
      </div>
      {exps.map((e) => {
        const t = row.tile(e);
        return (
          <ImageViewer
            key={e.key}
            compact
            src={t.src}
            title={`${row.label} · ${e.label}`}
            downloadSrc={t.download}
            legend={row.legend}
            inlineLegend={false}
            aspectRatio={aspect}
            pixelated={t.pixelated}
          />
        );
      })}
    </>
  );
}
