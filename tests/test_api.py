import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from tests.create_test_shapefile import create_shapefile_zip

client = TestClient(app)

SAMPLE_DIR = Path(__file__).parent / "sample_data"
KML_PATH = SAMPLE_DIR / "sample_polygon.kml"
SHAPEFILE_ZIP_PATH = SAMPLE_DIR / "sample_shapefile.zip"


@pytest.fixture(scope="module", autouse=True)
def setup_test_files():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    if not SHAPEFILE_ZIP_PATH.exists():
        create_shapefile_zip(str(SHAPEFILE_ZIP_PATH))


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"


def test_upload_kml_file():
    with open(KML_PATH, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("sample_polygon.kml", f, "application/vnd.google-earth.kml+xml")}
        )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample_polygon.kml"
    assert data["feature_count"] == 3
    assert data["status"] == "COMPLETED"

    file_id = data["id"]

    # Retrieve info
    info_res = client.get(f"/api/files/{file_id}/")
    assert info_res.status_code == 200
    assert info_res.json()["id"] == file_id

    # Retrieve measurements
    meas_res = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_res.status_code == 200
    meas_data = meas_res.json()
    assert meas_data["total_features"] == 3
    assert len(meas_data["features"]) == 3
    assert meas_data["summary"]["total_area_sq_m"] > 0
    assert meas_data["summary"]["total_length_m"] > 0


def test_upload_shapefile_zip():
    with open(SHAPEFILE_ZIP_PATH, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("sample_shapefile.zip", f, "application/zip")}
        )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample_shapefile.zip"
    assert data["feature_count"] == 1
    assert data["status"] == "COMPLETED"

    file_id = data["id"]

    meas_res = client.get(f"/api/files/{file_id}/measurements/")
    assert meas_res.status_code == 200
    meas_data = meas_res.json()
    assert len(meas_data["features"]) == 1
    assert meas_data["features"][0]["geometry_type"] == "Polygon"


def test_upload_unsupported_file():
    response = client.post(
        "/api/files/",
        files={"file": ("invalid_doc.txt", b"Hello world", "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


def test_get_nonexistent_file():
    response = client.get("/api/files/nonexistent_id/")
    assert response.status_code == 404


def test_delete_file():
    with open(KML_PATH, "rb") as f:
        response = client.post(
            "/api/files/",
            files={"file": ("to_delete.kml", f, "application/vnd.google-earth.kml+xml")}
        )
    file_id = response.json()["id"]

    del_res = client.delete(f"/api/files/{file_id}/")
    assert del_res.status_code == 200

    get_res = client.get(f"/api/files/{file_id}/")
    assert get_res.status_code == 404
