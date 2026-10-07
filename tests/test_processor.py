import pytest
from shapely.geometry import Polygon, LineString, Point
from app.services.crs_transformer import get_utm_epsg_for_latlon, estimate_projected_crs, transform_geometry
from app.services.measurement_engine import MeasurementEngine


def test_utm_epsg_calculation():
    # Bangalore: lon=77.59, lat=12.97 -> UTM Zone 43N (EPSG:32643)
    epsg = get_utm_epsg_for_latlon(77.59, 12.97)
    assert epsg == "EPSG:32643"

    # Sydney: lon=151.20, lat=-33.86 -> UTM Zone 56S (EPSG:32756)
    epsg_sydney = get_utm_epsg_for_latlon(151.20, -33.86)
    assert epsg_sydney == "EPSG:32756"


def test_estimate_projected_crs():
    poly = Polygon([(77.5900, 12.9700), (77.5950, 12.9700), (77.5950, 12.9750), (77.5900, 12.9750)])
    proj_crs = estimate_projected_crs(poly, source_crs="EPSG:4326")
    assert proj_crs == "EPSG:32643"


def test_polygon_area_measurement():
    # Approx 500m x 550m polygon near Bangalore
    poly = Polygon([(77.5900, 12.9700), (77.5950, 12.9700), (77.5950, 12.9750), (77.5900, 12.9750)])
    result = MeasurementEngine.process_feature_measurement(
        feature_id="poly_1",
        geometry=poly,
        original_crs="EPSG:4326",
        properties={"name": "Test Zone"}
    )

    assert result["measurement_type"] == "area"
    assert result["value_sq_m"] > 0
    assert result["value_sq_km"] > 0
    assert "m²" in result["formatted"]
    assert result["projected_crs"] == "EPSG:32643"


def test_linestring_length_measurement():
    line = LineString([(77.5900, 12.9700), (77.5950, 12.9700)])
    result = MeasurementEngine.process_feature_measurement(
        feature_id="line_1",
        geometry=line,
        original_crs="EPSG:4326",
        properties={"name": "Access Road"}
    )

    assert result["measurement_type"] == "length"
    assert result["value_m"] > 0
    assert result["value_km"] > 0
    assert "m" in result["formatted"]


def test_point_measurement():
    pt = Point(77.5925, 12.9725)
    result = MeasurementEngine.process_feature_measurement(
        feature_id="pt_1",
        geometry=pt,
        original_crs="EPSG:4326",
        properties={"name": "Tower"}
    )

    assert result["measurement_type"] == "none"
    assert result["value_sq_m"] is None
    assert result["value_m"] is None
    assert "No measurement required" in result["formatted"]
