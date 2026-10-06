import { Play } from "lucide-react";
import type { ReactNode } from "react";
import type { AnalysisSettings, Angle, GrayLevels } from "../../types/analysis";
import { Button } from "../common/Button";
import { InfoTooltip } from "../common/Tooltip";

const WINDOW_SIZES = [3, 5, 7, 9, 11, 13, 15];
const GRAY_LEVELS: GrayLevels[] = [4, 8, 16, 32];
const ANGLES: Angle[] = [0, 45, 90, 135];
const ANGLE_OFFSETS: Record<Angle, string> = { 0: "(0, d)", 45: "(−d, d)", 90: "(−d, 0)", 135: "(−d, −d)" };

export function validateSettings(s: AnalysisSettings): string | null {
  if (s.glcmWindowSize % 2 === 0 || s.glcmWindowSize < 3 || s.glcmWindowSize > 15) return "Window size must be odd (3–15).";
  if (!Number.isInteger(s.distance) || s.distance < 1) return "Distance must be a positive integer.";
  if (s.distance >= s.glcmWindowSize) return "Distance must be smaller than the window size.";
  if (!Number.isInteger(s.clusters) || s.clusters < 2 || s.clusters > 10) return "Clusters must be between 2 and 10.";
  if (!Number.isInteger(s.randomState) || s.randomState < 0) return "Random state must be a non-negative integer.";
  return null;
}

function Field({ label, tip, htmlFor, children }: { label: string; tip: ReactNode; htmlFor?: string; children: ReactNode }) {
  return (
    <div>
      <div className="mb-1 flex items-center gap-1.5">
        <label htmlFor={htmlFor} className="text-xs font-medium text-slate-700">
          {label}
        </label>
        <InfoTooltip>{tip}</InfoTooltip>
      </div>
      {children}
    </div>
  );
}

const inputCls =
  "num h-8 w-full rounded-md border border-slate-300 bg-white px-2 text-sm text-slate-900 disabled:bg-slate-50 disabled:text-slate-400";

interface ParameterPanelProps {
  value: AnalysisSettings;
  onChange: (next: AnalysisSettings) => void;
  onRun: () => void;
  smoothingSizes: number[];
  disabled: boolean;
  running: boolean;
  canRun: boolean;
}

export function ParameterPanel({ value, onChange, onRun, smoothingSizes, disabled, running, canRun }: ParameterPanelProps) {
  const set = <K extends keyof AnalysisSettings>(key: K, v: AnalysisSettings[K]) => onChange({ ...value, [key]: v });
  const error = validateSettings(value);
  const pairs = value.angle === 0 || value.angle === 90
    ? value.glcmWindowSize * (value.glcmWindowSize - value.distance)
    : (value.glcmWindowSize - value.distance) ** 2;

  return (
    <div className="flex flex-col gap-5">
      <fieldset disabled={disabled} className="flex flex-col gap-4">
        <legend className="label-caps mb-3">GLCM parameters</legend>
        <div className="grid grid-cols-2 gap-3">
          <Field
            label="Window size"
            htmlFor="p-window"
            tip="Side length of the moving window. A separate GLCM is built for the w × w neighbourhood of every pixel. Larger windows give smoother, more stable texture estimates but blur boundaries."
          >
            <select
              id="p-window"
              className={inputCls}
              value={value.glcmWindowSize}
              onChange={(e) => set("glcmWindowSize", Number(e.target.value))}
            >
              {WINDOW_SIZES.map((w) => (
                <option key={w} value={w}>
                  {w} × {w}
                </option>
              ))}
            </select>
          </Field>
          <Field
            label="Gray levels"
            htmlFor="p-levels"
            tip="The image is quantized to L levels before building the GLCM (an L × L matrix). Fewer levels give better-populated matrices for small windows; 8 or 16 is typical."
          >
            <select
              id="p-levels"
              className={inputCls}
              value={value.grayLevels}
              onChange={(e) => set("grayLevels", Number(e.target.value) as GrayLevels)}
            >
              {GRAY_LEVELS.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </Field>
          <Field
            label="Distance (d)"
            htmlFor="p-distance"
            tip="Pixel distance between the reference pixel and its neighbour in each co-occurrence pair. Must be smaller than the window size."
          >
            <input
              id="p-distance"
              type="number"
              min={1}
              max={value.glcmWindowSize - 1}
              step={1}
              className={inputCls}
              value={value.distance}
              onChange={(e) => set("distance", Math.trunc(Number(e.target.value)))}
            />
          </Field>
          <Field
            label="Pairs per window"
            tip="Number of valid pixel pairs counted in every local GLCM (both pixels must lie inside the window). Derived from the window size, distance and angle."
          >
            <div className="num flex h-8 items-center rounded-md border border-slate-200 bg-slate-50 px-2 text-sm text-slate-600">
              {pairs > 0 ? pairs : "—"}
            </div>
          </Field>
        </div>

        <Field
          label="Angle (θ)"
          tip="Direction of the neighbour. 0° compares each pixel with the pixel to its right, 90° with the pixel above, 45° and 135° along the diagonals."
        >
          <div role="radiogroup" aria-label="Angle" className="grid grid-cols-4 overflow-hidden rounded-md border border-slate-300">
            {ANGLES.map((a) => (
              <button
                key={a}
                type="button"
                role="radio"
                aria-checked={value.angle === a}
                onClick={() => set("angle", a)}
                className={`h-8 border-l border-slate-300 text-sm first:border-l-0 disabled:cursor-not-allowed disabled:opacity-50 ${
                  value.angle === a ? "bg-slate-900 font-medium text-white" : "bg-white text-slate-700 hover:bg-slate-50"
                }`}
              >
                {a}°
              </button>
            ))}
          </div>
          <p className="num mt-1 text-[11px] text-slate-500">
            offset (Δrow, Δcol) = {ANGLE_OFFSETS[value.angle].replaceAll("d", String(value.distance))}
          </p>
        </Field>
      </fieldset>

      <div className="border-t border-slate-200 pt-4">
      <fieldset disabled={disabled} className="flex flex-col gap-3">
        <legend className="label-caps mb-3">K-Means</legend>
        <div className="grid grid-cols-2 gap-3">
          <Field
            label="Clusters (K)"
            htmlFor="p-k"
            tip="Number of texture groups. Each pixel's standardized [ASM, Contrast, Mean] vector is assigned to one of K clusters."
          >
            <input
              id="p-k"
              type="number"
              min={2}
              max={10}
              step={1}
              className={inputCls}
              value={value.clusters}
              onChange={(e) => set("clusters", Math.trunc(Number(e.target.value)))}
            />
          </Field>
          <Field
            label="Random state"
            htmlFor="p-seed"
            tip="Seed for K-Means centroid initialisation (10 initialisations are run). The same seed reproduces the same clustering."
          >
            <input
              id="p-seed"
              type="number"
              min={0}
              step={1}
              className={inputCls}
              value={value.randomState}
              onChange={(e) => set("randomState", Math.trunc(Number(e.target.value)))}
            />
          </Field>
        </div>
      </fieldset>
      </div>

      <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
        <span className="font-medium text-slate-700">Experiments:</span> original image and{" "}
        {smoothingSizes.map((s) => `${s}×${s}`).join(" and ")} averaging, all processed with identical parameters.
      </div>

      {error && <p className="text-xs text-red-700">{error}</p>}

      <Button
        variant="primary"
        size="lg"
        className="w-full"
        disabled={!canRun || error !== null || running}
        onClick={onRun}
        icon={<Play className="h-4 w-4" aria-hidden />}
      >
        {running ? "Analysis running…" : "Run Analysis"}
      </Button>
    </div>
  );
}
