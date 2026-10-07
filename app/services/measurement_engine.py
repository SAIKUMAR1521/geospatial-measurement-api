from typing import Dict, Any
from shapely.geometry import base, MultiPolygon, MultiLineString, MultiPoint, GeometryCollection
from shapely.validation import make_valid
from app.services.crs_transformer import estimate_projected_crs, transform_geometry


class MeasurementEngine:
    """Core measurement engine for geospatial geometries."""

    @classmethod
    def process_feature_measurement(
        cls,
        feature_id: Any,
        geometry: base.BaseGeometry,
        original_crs: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Processes a geometry:
        1. Validates geometry.
        2. Determines optimal projected CRS (UTM).
        3. Reprojects geometry to projected CRS.
        4. Calculates area/length based on geometry type.
        """
        if geometry is None or geometry.is_empty:
            return {
                "feature_id": feature_id,
                "geometry_type": "Unknown",
                "original_crs": original_crs,
                "projected_crs": original_crs,
                "measurement_type": "none",
                "formatted": "Empty or Null Geometry",
                "properties": properties,
                "geometry_summary": "EMPTY"
            }

        # Validate geometry if invalid
        if not geometry.is_valid:
            try:
                geometry = make_valid(geometry)
            except Exception:
                pass

        geom_type = geometry.geom_type

        # Estimate optimal projected CRS (UTM zone)
        projected_crs = estimate_projected_crs(geometry, source_crs=original_crs)

        # Reproject geometry to projected CRS
        projected_geom = transform_geometry(geometry, source_crs=original_crs, target_crs=projected_crs)

        if geom_type in ["Polygon", "MultiPolygon"]:
            area_sq_m = float(projected_geom.area)
            area_sq_km = area_sq_m / 1_000_000.0
            formatted = f"{area_sq_m:,.2f} m² ({area_sq_km:,.4f} km²)"

            return {
                "feature_id": feature_id,
                "geometry_type": geom_type,
                "original_crs": original_crs,
                "projected_crs": projected_crs,
                "measurement_type": "area",
                "value_sq_m": round(area_sq_m, 2),
                "value_sq_km": round(area_sq_km, 6),
                "value_m": None,
                "value_km": None,
                "formatted": formatted,
                "properties": properties,
                "geometry_summary": f"Centroid: ({geometry.centroid.x:.4f}, {geometry.centroid.y:.4f})"
            }

        elif geom_type in ["LineString", "MultiLineString"]:
            length_m = float(projected_geom.length)
            length_km = length_m / 1000.0
            formatted = f"{length_m:,.2f} m ({length_km:,.4f} km)"

            return {
                "feature_id": feature_id,
                "geometry_type": geom_type,
                "original_crs": original_crs,
                "projected_crs": projected_crs,
                "measurement_type": "length",
                "value_sq_m": None,
                "value_sq_km": None,
                "value_m": round(length_m, 2),
                "value_km": round(length_km, 4),
                "formatted": formatted,
                "properties": properties,
                "geometry_summary": f"Centroid: ({geometry.centroid.x:.4f}, {geometry.centroid.y:.4f})"
            }

        elif geom_type in ["Point", "MultiPoint"]:
            return {
                "feature_id": feature_id,
                "geometry_type": geom_type,
                "original_crs": original_crs,
                "projected_crs": projected_crs,
                "measurement_type": "none",
                "value_sq_m": None,
                "value_sq_km": None,
                "value_m": None,
                "value_km": None,
                "formatted": f"Point location ({geometry.centroid.x:.4f}, {geometry.centroid.y:.4f}) - No measurement required",
                "properties": properties,
                "geometry_summary": f"Location: ({geometry.centroid.x:.4f}, {geometry.centroid.y:.4f})"
            }

        elif geom_type == "GeometryCollection":
            # Handle GeometryCollection safely
            total_area = 0.0
            total_length = 0.0
            for g in projected_geom.geoms:
                if g.geom_type in ["Polygon", "MultiPolygon"]:
                    total_area += g.area
                elif g.geom_type in ["LineString", "MultiLineString"]:
                    total_length += g.length

            if total_area > 0 and total_length > 0:
                formatted = f"Collection: Area={total_area:,.2f} m², Length={total_length:,.2f} m"
                m_type = "mixed"
            elif total_area > 0:
                formatted = f"Collection Area: {total_area:,.2f} m² ({total_area/1e6:,.4f} km²)"
                m_type = "area"
            elif total_length > 0:
                formatted = f"Collection Length: {total_length:,.2f} m ({total_length/1000:,.4f} km)"
                m_type = "length"
            else:
                formatted = "Collection (Points or empty)"
                m_type = "none"

            return {
                "feature_id": feature_id,
                "geometry_type": geom_type,
                "original_crs": original_crs,
                "projected_crs": projected_crs,
                "measurement_type": m_type,
                "value_sq_m": round(total_area, 2) if total_area > 0 else None,
                "value_sq_km": round(total_area / 1e6, 6) if total_area > 0 else None,
                "value_m": round(total_length, 2) if total_length > 0 else None,
                "value_km": round(total_length / 1000, 4) if total_length > 0 else None,
                "formatted": formatted,
                "properties": properties,
                "geometry_summary": "GeometryCollection"
            }

        else:
            # Fallback for any unknown or exotic geometry type
            return {
                "feature_id": feature_id,
                "geometry_type": geom_type,
                "original_crs": original_crs,
                "projected_crs": projected_crs,
                "measurement_type": "unsupported",
                "value_sq_m": None,
                "value_sq_km": None,
                "value_m": None,
                "value_km": None,
                "formatted": f"Geometry type '{geom_type}' measurement not supported",
                "properties": properties,
                "geometry_summary": geom_type
            }
