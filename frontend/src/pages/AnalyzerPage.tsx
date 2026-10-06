import { ArrowRight, RefreshCw } from "lucide-react";
import { useRef } from "react";
import { Button } from "../components/common/Button";
import { ErrorNotice } from "../components/common/ErrorNotice";
import { Panel } from "../components/common/Panel";
import { ParameterPanel } from "../components/parameters/ParameterPanel";
import { ProcessingStages } from "../components/processing/ProcessingStages";
import { ACCEPTED_EXTENSIONS, DropZone } from "../components/upload/DropZone";
import { ImageMetadataCard } from "../components/upload/ImageMetadataCard";
import { ImageViewer } from "../components/visualization/ImageViewer";
import type { AnalysisSettings, ImageMetadata, JobStatus } from "../types/analysis";

interface AnalyzerPageProps {
  image: ImageMetadata | null;
  uploading: boolean;
  uploadError: string | null;
  onUpload: (file: File) => void;
  settings: AnalysisSettings;
  onSettingsChange: (s: AnalysisSettings) => void;
  smoothingSizes: number[];
  onRun: () => void;
  runError: string | null;
  analysisActive: boolean;
  status: JobStatus | undefined;
  hasResults: boolean;
  onViewResults: () => void;
}

export function AnalyzerPage(props: AnalyzerPageProps) {
  const { image, uploading, uploadError, onUpload, status, analysisActive } = props;
  const changeRef = useRef<HTMLInputElement>(null);
  const showProcessing = analysisActive || status !== undefined;

  return (
    <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_400px]">
      <Panel
        title="1 · Input image"
        subtitle={image ? "Preview of the grayscale image used by the pipeline" : "Upload a remote-sensing image to begin"}
        actions={
          image && (
            <>
              <Button
                size="sm"
                icon={<RefreshCw className="h-3.5 w-3.5" aria-hidden />}
                disabled={uploading || analysisActive}
                onClick={() => changeRef.current?.click()}
              >
                {uploading ? "Uploading…" : "Change Image"}
              </Button>
              <input
                ref={changeRef}
                type="file"
                accept={ACCEPTED_EXTENSIONS.join(",")}
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) onUpload(f);
                  e.target.value = "";
                }}
              />
            </>
          )
        }
      >
        {uploadError && (
          <div className="mb-3">
            <ErrorNotice title="Upload failed" message={uploadError} />
          </div>
        )}
        {image ? (
          <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_240px]">
            <div className="mx-auto w-full max-w-[640px]">
              <ImageViewer
                src={image.previewUrl}
                title={image.filename}
                subtitle="8-bit display preview"
                aspectRatio={image.width / image.height}
                downloadSrc={null}
              />
            </div>
            <div>
              <p className="label-caps mb-1">Image metadata</p>
              <ImageMetadataCard meta={image} />
              <p className="mt-3 text-[11px] leading-relaxed text-slate-500">
                Statistics are computed on the grayscale array returned by the existing <code className="num">load_image()</code>,
                before quantization.
              </p>
            </div>
          </div>
        ) : (
          <DropZone onFile={onUpload} busy={uploading} />
        )}
      </Panel>

      <div className="flex flex-col gap-5">
        <Panel title="2 · Analysis parameters" subtitle="Applied identically to all three experiments">
          <ParameterPanel
            value={props.settings}
            onChange={props.onSettingsChange}
            onRun={props.onRun}
            smoothingSizes={props.smoothingSizes}
            disabled={analysisActive}
            running={analysisActive}
            canRun={image !== null && !uploading}
          />
          {!image && <p className="mt-2 text-center text-[11px] text-slate-500">Upload an image to enable the analysis.</p>}
          {props.runError && (
            <div className="mt-3">
              <ErrorNotice title="Could not start analysis" message={props.runError} />
            </div>
          )}
        </Panel>

        {showProcessing && (
          <Panel title="3 · Processing">
            <ProcessingStages status={status} />
            {status?.state === "failed" && status.error && (
              <div className="mt-3">
                <ErrorNotice title="The pipeline reported an error" message={status.error} />
              </div>
            )}
            {props.hasResults && status?.state === "completed" && (
              <Button
                variant="primary"
                className="mt-4 w-full"
                onClick={props.onViewResults}
                icon={<ArrowRight className="h-4 w-4" aria-hidden />}
              >
                View results
              </Button>
            )}
          </Panel>
        )}
      </div>
    </div>
  );
}
