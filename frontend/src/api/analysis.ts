import { getJson, postForm, postJson } from "./client";
import type {
  AnalysisCreated,
  AnalysisParameters,
  AnalysisResult,
  ApiDefaults,
  ImageMetadata,
  JobStatus,
} from "../types/analysis";

export function getDefaults(): Promise<ApiDefaults> {
  return getJson<ApiDefaults>("/api/config");
}

export function uploadImage(file: File): Promise<ImageMetadata> {
  const form = new FormData();
  form.append("file", file);
  return postForm<ImageMetadata>("/api/upload", form);
}

export function runAnalysis(params: AnalysisParameters): Promise<AnalysisCreated> {
  return postJson<AnalysisCreated>("/api/analyze", params);
}

export function getAnalysisStatus(analysisId: string): Promise<JobStatus> {
  return getJson<JobStatus>(`/api/analysis/${analysisId}/status`);
}

export function getAnalysisResults(analysisId: string): Promise<AnalysisResult> {
  return getJson<AnalysisResult>(`/api/analysis/${analysisId}/results`);
}

/** URL that makes the backend send a generated file as an attachment. */
export function downloadUrl(fileUrl: string): string {
  return `${fileUrl}${fileUrl.includes("?") ? "&" : "?"}download=true`;
}

/** Trigger a browser download for a backend file URL. */
export function downloadResult(fileUrl: string): void {
  const a = document.createElement("a");
  a.href = downloadUrl(fileUrl);
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
}
