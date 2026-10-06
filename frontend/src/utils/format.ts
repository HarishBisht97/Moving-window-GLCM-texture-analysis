import type { FeatureKey } from "../types/analysis";

export const FEATURE_LABELS: Record<FeatureKey, string> = {
  ASM: "ASM",
  CON: "Contrast",
  MEAN: "Mean",
};

export const FEATURE_ORDER: FeatureKey[] = ["ASM", "CON", "MEAN"];

/** Fixed-precision number for scientific tables (switches to exponent for tiny values). */
export function fmt(value: number, digits = 4): string {
  if (!Number.isFinite(value)) return "—";
  if (value !== 0 && Math.abs(value) < 10 ** -digits) return value.toExponential(2);
  return value.toFixed(digits);
}

export function fmtInt(value: number): string {
  return value.toLocaleString("en-US");
}

export function fmtPercent(value: number, digits = 1): string {
  return `${value.toFixed(digits)}%`;
}

/** Relative change from `from` to `to` in percent, or null when undefined. */
export function percentChange(from: number, to: number): number | null {
  if (Math.abs(from) < 1e-12) return null;
  return ((to - from) / Math.abs(from)) * 100;
}

export function fmtChange(change: number | null): string {
  if (change === null) return "n/a";
  if (Math.abs(change) < 0.05) return "0.0%";
  const sign = change > 0 ? "+" : "";
  return `${sign}${change.toFixed(1)}%`;
}

export function fmtBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** Short case label used in compact headers: "Original", "7×7", "9×9". */
export function shortCase(label: string, smoothingSize: number | null): string {
  return smoothingSize ? `${smoothingSize}×${smoothingSize}` : label;
}
