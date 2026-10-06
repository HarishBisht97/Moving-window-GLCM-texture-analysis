import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { Header } from "./components/layout/Header";
import { WorkflowStepper, type StepId } from "./components/layout/WorkflowStepper";
import { useAnalysisResults, useAnalysisStatus, useDefaults, useRunAnalysis, useUpload } from "./hooks/useAnalysis";
import { AnalyzerPage } from "./pages/AnalyzerPage";
import { ResultsPage } from "./pages/ResultsPage";

const ComparisonPage = lazy(() => import("./pages/ComparisonPage").then((m) => ({ default: m.ComparisonPage })));
import type { AnalysisSettings, ImageMetadata } from "./types/analysis";

const FALLBACK_SETTINGS: AnalysisSettings = {
  glcmWindowSize: 7,
  grayLevels: 8,
  distance: 1,
  angle: 0,
  clusters: 4,
  randomState: 0,
};

type View = "analyzer" | "results" | "compare";

export default function App() {
  const defaults = useDefaults();
  const upload = useUpload();
  const run = useRunAnalysis();

  const [image, setImage] = useState<ImageMetadata | null>(null);
  const [settings, setSettings] = useState<AnalysisSettings>(FALLBACK_SETTINGS);
  const [settingsTouched, setSettingsTouched] = useState(false);
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [view, setView] = useState<View>("analyzer");

  useEffect(() => {
    const d = defaults.data;
    if (d && !settingsTouched) {
      setSettings({
        glcmWindowSize: d.glcmWindowSize,
        grayLevels: d.grayLevels,
        distance: d.distance,
        angle: d.angle,
        clusters: d.clusters,
        randomState: d.randomState,
      });
    }
  }, [defaults.data, settingsTouched]);

  const status = useAnalysisStatus(analysisId);
  const jobState = status.data?.state;
  const results = useAnalysisResults(analysisId, jobState === "completed");
  const analysisActive = analysisId !== null && (jobState === undefined || jobState === "queued" || jobState === "running");

  useEffect(() => {
    if (results.data) setView("results");
  }, [results.data]);

  const handleUpload = (file: File) => {
    upload.mutate(file, {
      onSuccess: (meta) => {
        setImage(meta);
        setAnalysisId(null);
        setView("analyzer");
      },
    });
  };

  const handleRun = () => {
    if (!image) return;
    run.mutate({ imageId: image.imageId, ...settings }, { onSuccess: ({ analysisId: id }) => setAnalysisId(id) });
  };

  const currentStep: StepId =
    view === "results" ? "results" : view === "compare" ? "compare" : !image ? "upload" : analysisActive ? "run" : "configure";

  const { completed, enabled } = useMemo(() => {
    const done = new Set<StepId>();
    const on = new Set<StepId>(["upload"]);
    if (image) {
      done.add("upload");
      on.add("configure");
    }
    if (analysisId) {
      done.add("configure");
      on.add("run");
    }
    if (results.data) {
      done.add("configure");
      done.add("run");
      on.add("results");
      on.add("compare");
    }
    if (view === "compare") done.add("results");
    return { completed: done, enabled: on };
  }, [image, analysisId, results.data, view]);

  const selectStep = (step: StepId) => {
    if (step === "results") setView("results");
    else if (step === "compare") setView("compare");
    else setView("analyzer");
  };

  const smoothingSizes = defaults.data?.smoothingSizes ?? [7, 9];

  return (
    <div className="flex min-h-screen flex-col">
      <Header>
        {defaults.isError && (
          <p className="rounded border border-amber-300 bg-amber-50 px-2 py-1 text-xs text-amber-800">
            Backend not reachable at /api. Start it with uvicorn on port 8000.
          </p>
        )}
      </Header>
      <WorkflowStepper current={currentStep} completed={completed} enabled={enabled} onSelect={selectStep} />
      <main className="mx-auto w-full max-w-[1440px] flex-1 px-6 py-5">
        {view === "analyzer" && (
          <AnalyzerPage
            image={image}
            uploading={upload.isPending}
            uploadError={upload.error?.message ?? null}
            onUpload={handleUpload}
            settings={settings}
            onSettingsChange={(s) => {
              setSettingsTouched(true);
              setSettings(s);
            }}
            smoothingSizes={smoothingSizes}
            onRun={handleRun}
            runError={run.error?.message ?? null}
            analysisActive={analysisActive}
            status={status.data}
            hasResults={results.data !== undefined}
            onViewResults={() => setView("results")}
          />
        )}
        {view === "results" && results.data && (
          <ResultsPage result={results.data} onCompare={() => setView("compare")} />
        )}
        {view === "compare" && results.data && (
          <Suspense fallback={<p className="py-10 text-center text-xs text-slate-500">Loading comparison…</p>}>
            <ComparisonPage result={results.data} />
          </Suspense>
        )}
        {results.isError && (
          <p className="mt-4 text-xs text-red-700">Could not load results: {results.error.message}</p>
        )}
      </main>
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1440px] flex-wrap justify-between gap-2 px-6 py-2 text-[11px] text-slate-500">
          <span>GLCM features are computed locally for every moving-window position by the Python backend.</span>
          {results.data && (
            <span className="num">
              analysis {results.data.analysisId.slice(0, 8)} · {results.data.elapsedSeconds.toFixed(1)} s
            </span>
          )}
        </div>
      </footer>
    </div>
  );
}
