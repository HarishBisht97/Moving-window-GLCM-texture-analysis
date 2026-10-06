/** Types mirroring the FastAPI schemas in backend/schemas/analysis.py (camelCase JSON). */

export type FeatureKey = "ASM" | "CON" | "MEAN";
export type JobState = "queued" | "running" | "completed" | "failed";
export type StageState = "pending" | "active" | "done" | "failed";
export type GrayLevels = 4 | 8 | 16 | 32;
export type Angle = 0 | 45 | 90 | 135;

export interface ImageMetadata {
  imageId: string;
  filename: string;
  previewUrl: string;
  width: number;
  height: number;
  dataType: string;
  bands: number;
  min: number;
  max: number;
  mean: number;
  std: number;
}

export interface AnalysisParameters {
  imageId: string;
  glcmWindowSize: number;
  grayLevels: GrayLevels;
  distance: number;
  angle: Angle;
  clusters: number;
  randomState: number;
}

export type AnalysisSettings = Omit<AnalysisParameters, "imageId">;

export interface AnalysisCreated {
  analysisId: string;
}

export interface StageStatus {
  id: string;
  label: string;
  state: StageState;
}

export interface JobStatus {
  analysisId: string;
  state: JobState;
  stages: StageStatus[];
  error: string | null;
  elapsedSeconds: number | null;
}

export interface ColorLegend {
  kind: "continuous" | "categorical";
  colormap: string | null;
  vmin: number | null;
  vmax: number | null;
  clippedMax: boolean;
  colors: string[];
  labels: string[] | null;
}

export interface TextureStatistics {
  min: number;
  max: number;
  mean: number;
  std: number;
}

export interface TextureResult {
  feature: FeatureKey;
  title: string;
  imageUrl: string;
  figureUrl: string | null;
  statistics: TextureStatistics;
  legend: ColorLegend;
}

export interface ClusterStatistics {
  cluster: number;
  pixels: number;
  percent: number;
  centerAsm: number;
  centerCon: number;
  centerMean: number;
}

export interface ExperimentResult {
  key: string;
  label: string;
  prefix: string;
  smoothingSize: number | null;
  inputImageUrl: string;
  kmeansImageUrl: string;
  kmeansLegend: ColorLegend;
  textures: TextureResult[];
  clusters: ClusterStatistics[];
  inertia: number;
}

export interface FeatureStatisticsRow extends TextureStatistics {
  case: string;
  feature: FeatureKey;
}

export type DownloadCategory = "image" | "texture" | "cluster" | "figure" | "table" | "text";

export interface DownloadFile {
  name: string;
  label: string;
  category: DownloadCategory;
  sizeBytes: number;
  url: string;
}

export type MetricsRow = Record<string, number | string>;

export interface AnalysisResult {
  analysisId: string;
  image: ImageMetadata;
  parameters: AnalysisParameters;
  smoothingSizes: number[];
  experiments: ExperimentResult[];
  featureStatistics: FeatureStatisticsRow[];
  metrics: MetricsRow[];
  interpretation: string;
  comparisonGridUrl: string | null;
  smoothingComparisonUrl: string | null;
  downloads: DownloadFile[];
  zipUrl: string;
  elapsedSeconds: number;
}

export interface ApiDefaults {
  glcmWindowSize: number;
  grayLevels: GrayLevels;
  distance: number;
  angle: Angle;
  clusters: number;
  randomState: number;
  smoothingSizes: number[];
  allowedExtensions: string[];
}
