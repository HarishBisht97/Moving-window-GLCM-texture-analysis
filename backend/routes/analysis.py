from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from backend.schemas.analysis import (AnalysisCreated, AnalysisParameters, AnalysisResult,
                                      JobStatus)
from backend.services import analysis, images

router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", status_code=202, response_model=AnalysisCreated,
             response_model_by_alias=True)
def analyze(params: AnalysisParameters):
    try:
        return AnalysisCreated(analysis_id=analysis.start_analysis(params))
    except images.ImageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/analysis/{analysis_id}/status", response_model=JobStatus,
            response_model_by_alias=True)
def analysis_status(analysis_id: str):
    try:
        return analysis.get_status(analysis_id)
    except analysis.AnalysisError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/analysis/{analysis_id}/results", response_model=AnalysisResult,
            response_model_by_alias=True)
def analysis_results(analysis_id: str):
    try:
        return analysis.get_result(analysis_id)
    except analysis.AnalysisNotReady as exc:
        raise HTTPException(status_code=409, detail=f"Analysis is {exc}") from exc
    except analysis.AnalysisError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/analysis/{analysis_id}/files/{name:path}")
def analysis_file(analysis_id: str, name: str, download: bool = False):
    try:
        path = analysis.resolve_file(analysis_id, name)
    except analysis.AnalysisError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(path, filename=path.name if download else None,
                        content_disposition_type="attachment" if download else "inline")


@router.get("/analysis/{analysis_id}/download.zip")
def analysis_zip(analysis_id: str):
    try:
        buf = analysis.build_zip(analysis_id)
    except analysis.AnalysisError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StreamingResponse(
        buf, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="glcm_results_{analysis_id[:8]}.zip"'})
