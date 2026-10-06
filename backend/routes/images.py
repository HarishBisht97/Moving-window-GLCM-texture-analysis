from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse

from backend.schemas.analysis import ImageMetadata
from backend.services import images

router = APIRouter(prefix="/api", tags=["images"])


@router.post("/upload", response_model=ImageMetadata, response_model_by_alias=True)
async def upload_image(file: UploadFile = File(...)):
    data = await file.read()
    try:
        return await run_in_threadpool(images.save_upload, file.filename, data)
    except images.ImageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/images/{image_id}", response_model=ImageMetadata, response_model_by_alias=True)
def image_metadata(image_id: str):
    try:
        return images.get_metadata(image_id)
    except images.ImageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/images/{image_id}/preview")
def image_preview(image_id: str):
    try:
        return FileResponse(images.preview_path(image_id), media_type="image/png")
    except images.ImageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
