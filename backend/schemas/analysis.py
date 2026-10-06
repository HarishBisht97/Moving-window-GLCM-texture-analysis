"""API schemas. JSON uses camelCase; Python uses snake_case."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

import config

FeatureKey = Literal["ASM", "CON", "MEAN"]
JobState = Literal["queued", "running", "completed", "failed"]
StageState = Literal["pending", "active", "done", "failed"]


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ImageMetadata(ApiModel):
    image_id: str
    filename: str
    preview_url: str
    width: int
    height: int
    data_type: str
    bands: int
    min: float
    max: float
    mean: float
    std: float


class AnalysisParameters(ApiModel):
    image_id: str
    glcm_window_size: int = Field(config.GLCM_WINDOW_SIZE, ge=3, le=15)
    gray_levels: Literal[4, 8, 16, 32] = config.GRAY_LEVELS
    distance: int = Field(config.DISTANCE, ge=1, le=7)
    angle: Literal[0, 45, 90, 135] = config.ANGLE
    clusters: int = Field(config.NUM_CLUSTERS, ge=2, le=10)
    random_state: int = Field(config.RANDOM_STATE, ge=0, le=2**31 - 1)

    @model_validator(mode="after")
    def _check(self):
        if self.glcm_window_size % 2 == 0:
            raise ValueError("glcmWindowSize must be odd")
        if self.distance >= self.glcm_window_size:
            raise ValueError("distance must be smaller than glcmWindowSize")
        return self


class AnalysisCreated(ApiModel):
    analysis_id: str


class StageStatus(ApiModel):
    id: str
    label: str
    state: StageState


class JobStatus(ApiModel):
    analysis_id: str
    state: JobState
    stages: list[StageStatus]
    error: str | None = None
    elapsed_seconds: float | None = None


class ColorLegend(ApiModel):
    kind: Literal["continuous", "categorical"]
    colormap: str | None = None
    vmin: float | None = None
    vmax: float | None = None
    clipped_max: bool = False
    colors: list[str]
    labels: list[str] | None = None


class TextureStatistics(ApiModel):
    min: float
    max: float
    mean: float
    std: float


class TextureResult(ApiModel):
    feature: FeatureKey
    title: str
    image_url: str
    figure_url: str | None = None
    statistics: TextureStatistics
    legend: ColorLegend


class ClusterStatistics(ApiModel):
    cluster: int
    pixels: int
    percent: float
    center_asm: float
    center_con: float
    center_mean: float


class ExperimentResult(ApiModel):
    key: str
    label: str
    prefix: str
    smoothing_size: int | None
    input_image_url: str
    kmeans_image_url: str
    kmeans_legend: ColorLegend
    textures: list[TextureResult]
    clusters: list[ClusterStatistics]
    inertia: float


class FeatureStatisticsRow(ApiModel):
    case: str
    feature: FeatureKey
    min: float
    max: float
    mean: float
    std: float


class DownloadFile(ApiModel):
    name: str
    label: str
    category: Literal["image", "texture", "cluster", "figure", "table", "text"]
    size_bytes: int
    url: str


class AnalysisResult(ApiModel):
    analysis_id: str
    image: ImageMetadata
    parameters: AnalysisParameters
    smoothing_sizes: list[int]
    experiments: list[ExperimentResult]
    feature_statistics: list[FeatureStatisticsRow]
    metrics: list[dict[str, float | str]]
    interpretation: str
    comparison_grid_url: str | None
    smoothing_comparison_url: str | None
    downloads: list[DownloadFile]
    zip_url: str
    elapsed_seconds: float
