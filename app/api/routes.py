import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from typing import List

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS
from app.api.models import FileInfoResponse, FileMeasurementsResponse, FileListResponse
from app.services.file_processor import FileProcessor
from app.storage.file_store import file_store

router = APIRouter(prefix="/api/files", tags=["Geospatial Files"])


@router.post("/", response_model=FileInfoResponse, status_code=status.HTTP_201_CREATED)
async def upload_and_process_file(file: UploadFile = File(...)):
    """
    Uploads and processes a geospatial file (.zip containing Shapefile or .kml).
    Extracts features, identifies CRS, and calculates measurements.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing in request.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    file_id = uuid.uuid4().hex[:8]
    saved_filename = f"{file_id}_{file.filename}"
    saved_filepath = UPLOAD_DIR / saved_filename

    try:
        with open(saved_filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    try:
        record = FileProcessor.process_uploaded_file(file_id, str(saved_filepath), file.filename)
        return FileInfoResponse(
            id=record["id"],
            filename=record["filename"],
            feature_count=record["feature_count"],
            crs=record["crs"],
            status=record["status"],
            created_at=record["created_at"],
            error_message=record.get("error_message")
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error processing geospatial file: {str(e)}")


@router.get("/{id}/", response_model=FileInfoResponse)
async def get_file_info(id: str):
    """
    Retrieves metadata information for an uploaded file.
    """
    record = file_store.get_file_record(id)
    if not record:
        raise HTTPException(status_code=404, detail=f"File with ID '{id}' not found.")

    return FileInfoResponse(
        id=record["id"],
        filename=record["filename"],
        feature_count=record["feature_count"],
        crs=record["crs"],
        status=record["status"],
        created_at=record["created_at"],
        error_message=record.get("error_message")
    )


@router.get("/{id}/measurements/", response_model=FileMeasurementsResponse)
async def get_file_measurements(id: str):
    """
    Retrieves feature-by-feature measurement data for an uploaded file.
    """
    record = file_store.get_file_record(id)
    if not record:
        raise HTTPException(status_code=404, detail=f"File with ID '{id}' not found.")

    return FileMeasurementsResponse(
        file_id=record["id"],
        filename=record["filename"],
        status=record["status"],
        total_features=record["feature_count"],
        summary=record.get("summary", {}),
        features=record.get("features", [])
    )


@router.get("/", response_model=FileListResponse)
async def list_files():
    """
    Lists all uploaded files and their current status.
    """
    records = file_store.list_files()
    files_info = [
        FileInfoResponse(
            id=r["id"],
            filename=r["filename"],
            feature_count=r["feature_count"],
            crs=r["crs"],
            status=r["status"],
            created_at=r["created_at"],
            error_message=r.get("error_message")
        )
        for r in records
    ]
    return FileListResponse(total=len(files_info), files=files_info)


@router.delete("/{id}/", status_code=status.HTTP_200_OK)
async def delete_file(id: str):
    """
    Deletes an uploaded file and its metadata.
    """
    success = file_store.delete_file(id)
    if not success:
        raise HTTPException(status_code=404, detail=f"File with ID '{id}' not found.")
    return {"detail": f"File '{id}' deleted successfully."}
