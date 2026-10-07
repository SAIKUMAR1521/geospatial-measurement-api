import os
import zipfile
import tempfile
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

import geopandas as gpd
from shapely.geometry import shape

from app.config import UPLOAD_DIR
from app.services.kml_parser import KMLParser
from app.services.measurement_engine import MeasurementEngine
from app.services.crs_transformer import normalize_crs_string
from app.storage.file_store import file_store


class FileProcessor:
    """Orchestrates geospatial file extraction, parsing, measurement, and persistence."""

    @classmethod
    def process_uploaded_file(cls, file_id: str, file_path: str, original_filename: str) -> Dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        ext = Path(original_filename).suffix.lower()

        rel_filepath = str(Path("uploads") / Path(file_path).name)

        # Initial pending record
        file_record = {
            "id": file_id,
            "filename": original_filename,
            "filepath": rel_filepath,
            "feature_count": 0,
            "crs": "EPSG:4326",
            "status": "PROCESSING",
            "created_at": created_at,
            "error_message": None,
            "summary": {
                "total_area_sq_m": 0.0,
                "total_area_sq_km": 0.0,
                "total_length_m": 0.0,
                "total_length_km": 0.0,
                "geometry_counts": {},
                "default_projected_crs": "EPSG:3857"
            },
            "features": []
        }
        file_store.save_file_record(file_id, file_record)

        try:
            if ext == ".zip":
                features_raw, detected_crs = cls._process_shapefile_zip(file_path, file_id)
            elif ext == ".kml":
                features_raw, detected_crs = cls._process_kml(file_path)
            else:
                raise ValueError(f"Unsupported file extension: {ext}. Only .zip (Shapefile) and .kml are allowed.")

            if not features_raw:
                file_record["status"] = "COMPLETED"
                file_record["crs"] = detected_crs
                file_store.save_file_record(file_id, file_record)
                return file_record

            # Process measurements
            processed_features = []
            total_area_m2 = 0.0
            total_length_m = 0.0
            geom_counts = {}
            primary_projected_crs = None

            for idx, feat in enumerate(features_raw):
                feat_id = feat.get("feature_id", idx)
                geometry = feat.get("geometry")
                props = feat.get("properties", {})
                orig_crs = feat.get("crs") or detected_crs

                meas = MeasurementEngine.process_feature_measurement(
                    feature_id=feat_id,
                    geometry=geometry,
                    original_crs=orig_crs,
                    properties=props
                )
                processed_features.append(meas)

                # Aggregate metrics
                gtype = meas["geometry_type"]
                geom_counts[gtype] = geom_counts.get(gtype, 0) + 1

                if meas["value_sq_m"] is not None:
                    total_area_m2 += meas["value_sq_m"]
                if meas["value_m"] is not None:
                    total_length_m += meas["value_m"]

                if primary_projected_crs is None and meas["projected_crs"]:
                    primary_projected_crs = meas["projected_crs"]

            file_record["status"] = "COMPLETED"
            file_record["feature_count"] = len(processed_features)
            file_record["crs"] = detected_crs
            file_record["summary"] = {
                "total_area_sq_m": round(total_area_m2, 2),
                "total_area_sq_km": round(total_area_m2 / 1_000_000.0, 6),
                "total_length_m": round(total_length_m, 2),
                "total_length_km": round(total_length_m / 1000.0, 4),
                "geometry_counts": geom_counts,
                "default_projected_crs": primary_projected_crs or "EPSG:3857"
            }
            file_record["features"] = processed_features
            file_store.save_file_record(file_id, file_record)

            return file_record

        except Exception as e:
            file_record["status"] = "FAILED"
            file_record["error_message"] = str(e)
            file_store.save_file_record(file_id, file_record)
            raise e

    @classmethod
    def _process_shapefile_zip(cls, zip_path: str, file_id: str):
        extract_dir = Path(UPLOAD_DIR) / f"temp_{file_id}"
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Find .shp file
            shp_files = list(extract_dir.rglob("*.shp"))
            if not shp_files:
                raise ValueError("Invalid Shapefile ZIP package: No '.shp' file found inside the archive.")

            shp_path = shp_files[0]
            gdf = gpd.read_file(shp_path)

            detected_crs = normalize_crs_string(gdf.crs)

            features = []
            for idx, row in gdf.iterrows():
                geom = row.geometry
                props = {k: v for k, v in row.items() if k != 'geometry'}
                # Clean up non-serializable property values
                clean_props = {}
                for k, v in props.items():
                    if isinstance(v, (int, float, str, bool)) or v is None:
                        clean_props[k] = v
                    else:
                        clean_props[k] = str(v)

                features.append({
                    "feature_id": idx,
                    "geometry": geom,
                    "geometry_type": geom.geom_type if geom else "Unknown",
                    "crs": detected_crs,
                    "properties": clean_props
                })

            return features, detected_crs

        finally:
            # Clean up temp extracted directory
            if extract_dir.exists():
                try:
                    shutil.rmtree(extract_dir)
                except Exception:
                    pass

    @classmethod
    def _process_kml(cls, kml_path: str):
        detected_crs = "EPSG:4326"
        features = []

        # Try GeoPandas first if driver is supported
        try:
            gdf = gpd.read_file(kml_path, driver='KML')
            if gdf.crs:
                detected_crs = normalize_crs_string(gdf.crs)

            for idx, row in gdf.iterrows():
                geom = row.geometry
                props = {k: v for k, v in row.items() if k != 'geometry'}
                clean_props = {k: (v if isinstance(v, (int, float, str, bool)) or v is None else str(v)) for k, v in props.items()}
                features.append({
                    "feature_id": clean_props.get("Name") or clean_props.get("name") or idx,
                    "geometry": geom,
                    "geometry_type": geom.geom_type if geom else "Unknown",
                    "crs": detected_crs,
                    "properties": clean_props
                })
            return features, detected_crs
        except Exception:
            # Fallback to robust xml KMLParser
            parsed = KMLParser.parse_kml_file(kml_path)
            return parsed, "EPSG:4326"
