import math
from typing import Tuple, Optional
from shapely.geometry import base, shape
from shapely.ops import transform
import pyproj


def get_utm_epsg_for_latlon(lon: float, lat: float) -> str:
    """
    Determines the EPSG code for the UTM Zone containing the given lon/lat point.
    UTM North zones: EPSG 32601 - 32660
    UTM South zones: EPSG 32701 - 32760
    """
    # Clamp longitude to [-180, 180]
    lon = ((lon + 180) % 360) - 180
    zone = int((lon + 180) / 6) + 1
    zone = min(max(zone, 1), 60)

    if lat >= 0:
        epsg_code = 32600 + zone
    else:
        epsg_code = 32700 + zone

    return f"EPSG:{epsg_code}"


def normalize_crs_string(crs_input) -> str:
    """Normalizes CRS string or PyProj CRS object into standard EPSG:XXXX format or WKT/string."""
    if crs_input is None:
        return "EPSG:4326"
    
    crs_str = str(crs_input).strip()
    if not crs_str:
        return "EPSG:4326"

    try:
        crs_obj = pyproj.CRS.from_user_input(crs_input)
        epsg = crs_obj.to_epsg()
        if epsg:
            return f"EPSG:{epsg}"
        return crs_obj.name or "EPSG:4326"
    except Exception:
        if "4326" in crs_str:
            return "EPSG:4326"
        if "3857" in crs_str:
            return "EPSG:3857"
        return crs_str


def estimate_projected_crs(geom: base.BaseGeometry, source_crs: str = "EPSG:4326") -> str:
    """
    Estimates the optimal projected coordinate reference system (UTM zone)
    for a given geometry based on its centroid.
    """
    if geom is None or geom.is_empty:
        return "EPSG:3857"

    norm_source = normalize_crs_string(source_crs)

    # Calculate centroid
    centroid = geom.centroid
    lon, lat = centroid.x, centroid.y

    # If source CRS is not EPSG:4326, transform centroid to EPSG:4326 first
    if norm_source != "EPSG:4326":
        try:
            transformer = pyproj.Transformer.from_crs(norm_source, "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(lon, lat)
        except Exception:
            pass

    # Ensure lat/lon are within valid ranges
    if not math.isnan(lon) and not math.isnan(lat):
        lat = max(min(lat, 89.9), -89.9)
        lon = max(min(lon, 179.9), -179.9)
        return get_utm_epsg_for_latlon(lon, lat)

    return "EPSG:3857"


def transform_geometry(geom: base.BaseGeometry, source_crs: str, target_crs: str) -> base.BaseGeometry:
    """
    Reprojects a Shapely geometry from source_crs to target_crs.
    """
    if geom is None or geom.is_empty:
        return geom

    source_norm = normalize_crs_string(source_crs)
    target_norm = normalize_crs_string(target_crs)

    if source_norm == target_norm:
        return geom

    try:
        transformer = pyproj.Transformer.from_crs(source_norm, target_norm, always_xy=True)
        try:
            from shapely import transform as shapely_transform
            def _proj_func(coords):
                res = transformer.transform(coords[:, 0], coords[:, 1])
                import numpy as np
                return np.column_stack(res)
            return shapely_transform(geom, _proj_func)
        except Exception:
            return transform(transformer.transform, geom)
    except Exception as e:
        print(f"Warning: Transformation failed from {source_crs} to {target_crs}: {e}")
        return geom
