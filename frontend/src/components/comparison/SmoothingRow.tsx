import type { AnalysisResult } from "../../types/analysis";
import { ImageViewer } from "../visualization/ImageViewer";

export function SmoothingRow({ result }: { result: AnalysisResult }) {
  const aspect = result.image.width / result.image.height;
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {result.experiments.map((e) => (
        <ImageViewer
          key={e.key}
          src={e.inputImageUrl}
          title={e.smoothingSize ? `${e.smoothingSize}×${e.smoothingSize} Averaging` : "Original Image"}
          subtitle={
            e.smoothingSize
              ? `Mean of N = ${e.smoothingSize * e.smoothingSize} pixels per output pixel`
              : `${result.image.width} × ${result.image.height} px grayscale`
          }
          aspectRatio={aspect}
        />
      ))}
    </div>
  );
}
