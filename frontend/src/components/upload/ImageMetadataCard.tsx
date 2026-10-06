import type { ImageMetadata } from "../../types/analysis";
import { fmt, fmtInt } from "../../utils/format";

export function ImageMetadataCard({ meta }: { meta: ImageMetadata }) {
  const rows: [string, string][] = [
    ["Filename", meta.filename],
    ["Dimensions", `${fmtInt(meta.width)} × ${fmtInt(meta.height)} px`],
    ["Data type", meta.bands > 1 ? `${meta.dataType} · ${meta.bands} bands → grayscale` : meta.dataType],
    ["Min", fmt(meta.min, 2)],
    ["Max", fmt(meta.max, 2)],
    ["Mean", fmt(meta.mean, 2)],
    ["Standard deviation", fmt(meta.std, 2)],
  ];
  return (
    <dl className="divide-y divide-slate-100 text-xs">
      {rows.map(([k, v]) => (
        <div key={k} className="flex items-baseline justify-between gap-4 py-1.5">
          <dt className="text-slate-500">{k}</dt>
          <dd className={`truncate text-right text-slate-900 ${k === "Filename" ? "font-medium" : "num"}`} title={v}>
            {v}
          </dd>
        </div>
      ))}
    </dl>
  );
}
