import { useMutation, useQuery } from "@tanstack/react-query";
import {
  getAnalysisResults,
  getAnalysisStatus,
  getDefaults,
  runAnalysis,
  uploadImage,
} from "../api/analysis";
import type { AnalysisParameters } from "../types/analysis";

export function useDefaults() {
  return useQuery({ queryKey: ["defaults"], queryFn: getDefaults, staleTime: Infinity, retry: 1 });
}

export function useUpload() {
  return useMutation({ mutationFn: (file: File) => uploadImage(file) });
}

export function useRunAnalysis() {
  return useMutation({ mutationFn: (params: AnalysisParameters) => runAnalysis(params) });
}

export function useAnalysisStatus(analysisId: string | null) {
  return useQuery({
    queryKey: ["analysis", analysisId, "status"],
    queryFn: () => getAnalysisStatus(analysisId as string),
    enabled: analysisId !== null,
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      return state === "completed" || state === "failed" ? false : 800;
    },
    refetchIntervalInBackground: true,
  });
}

export function useAnalysisResults(analysisId: string | null, ready: boolean) {
  return useQuery({
    queryKey: ["analysis", analysisId, "results"],
    queryFn: () => getAnalysisResults(analysisId as string),
    enabled: analysisId !== null && ready,
    staleTime: Infinity,
  });
}
