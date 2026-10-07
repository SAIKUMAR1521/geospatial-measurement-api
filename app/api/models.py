from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class FileInfoResponse(BaseModel):
    id: str = Field(..., description="Unique file identifier")
    filename: str = Field(..., description="Original uploaded filename")
    feature_count: int = Field(..., description="Total extracted geospatial features")
    crs: str = Field(..., description="Detected Coordinate Reference System (e.g. EPSG:4326)")
    status: str = Field(..., description="Processing status: COMPLETED, FAILED, PROCESSING")
    created_at: str = Field(..., description="Upload timestamp in ISO format")
    error_message: Optional[str] = Field(None, description="Error detail if status is FAILED")


class MeasurementDetail(BaseModel):
    feature_id: Any = Field(..., description="Index or identifier of the feature")
    geometry_type: str = Field(..., description="Geometry type (Polygon, LineString, Point, etc.)")
    original_crs: str = Field(..., description="Original CRS of the geometry")
    projected_crs: str = Field(..., description="Projected CRS used for metric calculation")
    measurement_type: str = Field(..., description="Type of measurement: area, length, none, unsupported")
    value_sq_m: Optional[float] = Field(None, description="Area in square meters (for Polygon)")
    value_sq_km: Optional[float] = Field(None, description="Area in square kilometers (for Polygon)")
    value_m: Optional[float] = Field(None, description="Length in meters (for LineString)")
    value_km: Optional[float] = Field(None, description="Length in kilometers (for LineString)")
    formatted: str = Field(..., description="Human-readable measurement summary")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Feature attributes/properties")
    geometry_summary: Optional[str] = Field(None, description="WKT or centroid summary of geometry")


class FileMeasurementsSummary(BaseModel):
    total_area_sq_m: float = Field(0.0, description="Sum of polygon areas in square meters")
    total_area_sq_km: float = Field(0.0, description="Sum of polygon areas in square kilometers")
    total_length_m: float = Field(0.0, description="Sum of line lengths in meters")
    total_length_km: float = Field(0.0, description="Sum of line lengths in kilometers")
    geometry_counts: Dict[str, int] = Field(default_factory=dict, description="Breakdown by geometry type")
    default_projected_crs: str = Field(..., description="Primary projected CRS used")


class FileMeasurementsResponse(BaseModel):
    file_id: str = Field(..., description="File ID")
    filename: str = Field(..., description="Filename")
    status: str = Field(..., description="Processing status")
    total_features: int = Field(..., description="Total feature count")
    summary: FileMeasurementsSummary
    features: List[MeasurementDetail] = Field(default_factory=list)


class FileListResponse(BaseModel):
    total: int
    files: List[FileInfoResponse]
