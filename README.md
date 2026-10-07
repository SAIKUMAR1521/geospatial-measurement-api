# Geospatial File Measurement API 🌍📏

A production-ready RESTful backend service built with **FastAPI**, **GeoPandas**, **Shapely**, and **PyProj**. The API enables users to upload geospatial vector files (Shapefile `.zip` packages and `.kml` files), automatically parses features, transforms geographic coordinate systems to optimal projected coordinate reference systems (Auto-UTM), and calculates exact spatial measurements (Area for Polygons, Length for LineStrings).

---

## 🚀 Setup & Local Installation

### Prerequisites
- **Python 3.10+** (Python 3.13 tested)
- `pip` package manager

### 1. Clone & Set Up Project Directory
```bash
git clone https://github.com/your-username/geospatial-measurement-api.git
cd geospatial-measurement-api
```

### 2. Create Virtual Environment
```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Backend Service
```bash
python run.py
# or using uvicorn directly:
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The application will be running at `http://127.0.0.1:8000`.

Interactive Swagger Documentation is accessible at:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 🧪 Running Automated Tests

Run the complete `pytest` test suite covering file uploads, KML parsing, Shapefile extraction, CRS auto-UTM transformation, and measurement logic:

```bash
pytest -v
```

---

## 📡 API Reference & Endpoints

### 1. Upload File
**`POST /api/files/`**
- **Content-Type**: `multipart/form-data`
- **Supported Formats**: `.zip` (containing `.shp`, `.shx`, `.dbf`), `.kml`
- **Sample Request (cURL)**:
  ```bash
  curl -X 'POST' \
    'http://127.0.0.1:8000/api/files/' \
    -H 'accept: application/json' \
    -H 'Content-Type: multipart/form-data' \
    -F 'file=@survey.kml'
  ```
- **Response (201 Created)**:
  ```json
  {
    "id": "a1b2c3d4",
    "filename": "survey.kml",
    "feature_count": 3,
    "crs": "EPSG:4326",
    "status": "COMPLETED",
    "created_at": "2026-10-07T21:15:00.000Z",
    "error_message": null
  }
  ```

---

### 2. Get File Information
**`GET /api/files/{id}/`**
- **Response (200 OK)**:
  ```json
  {
    "id": "a1b2c3d4",
    "filename": "survey.kml",
    "feature_count": 3,
    "crs": "EPSG:4326",
    "status": "COMPLETED",
    "created_at": "2026-10-07T21:15:00.000Z"
  }
  ```

---

### 3. Get Measurements
**`GET /api/files/{id}/measurements/`**
- **Response (200 OK)**:
  ```json
  {
    "file_id": "a1b2c3d4",
    "filename": "survey.kml",
    "status": "COMPLETED",
    "total_features": 3,
    "summary": {
      "total_area_sq_m": 250000.5,
      "total_area_sq_km": 0.250001,
      "total_length_m": 1500.75,
      "total_length_km": 1.5008,
      "geometry_counts": {
        "Polygon": 1,
        "LineString": 1,
        "Point": 1
      },
      "default_projected_crs": "EPSG:32643"
    },
    "features": [
      {
        "feature_id": "Survey Zone A",
        "geometry_type": "Polygon",
        "original_crs": "EPSG:4326",
        "projected_crs": "EPSG:32643",
        "measurement_type": "area",
        "value_sq_m": 250000.5,
        "value_sq_km": 0.250001,
        "value_m": null,
        "value_km": null,
        "formatted": "250,000.50 m² (0.2500 km²)",
        "properties": {
          "name": "Survey Zone A",
          "Owner": "Acme Agri Corp"
        },
        "geometry_summary": "Centroid: (77.5925, 12.9725)"
      },
      {
        "feature_id": "Access Road",
        "geometry_type": "LineString",
        "original_crs": "EPSG:4326",
        "projected_crs": "EPSG:32643",
        "measurement_type": "length",
        "value_sq_m": null,
        "value_sq_km": null,
        "value_m": 1500.75,
        "value_km": 1.5008,
        "formatted": "1,500.75 m (1.5008 km)",
        "properties": {
          "name": "Access Road"
        },
        "geometry_summary": "Centroid: (77.5925, 12.9725)"
      },
      {
        "feature_id": "Control Tower",
        "geometry_type": "Point",
        "original_crs": "EPSG:4326",
        "projected_crs": "EPSG:32643",
        "measurement_type": "none",
        "value_sq_m": null,
        "value_sq_km": null,
        "value_m": null,
        "value_km": null,
        "formatted": "Point location (77.5925, 12.9725) - No measurement required",
        "properties": {
          "name": "Control Tower"
        },
        "geometry_summary": "Location: (77.5925, 12.9725)"
      }
    ]
  }
  ```

---

### 4. List All Uploaded Files
**`GET /api/files/`**

---

### 5. Delete File
**`DELETE /api/files/{id}/`**

---

## 🏗️ Architecture & Component Design

```
                     ┌────────────────────────┐
                     │   Client Request       │
                     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │   FastAPI Routes       │
                     │  (app/api/routes.py)   │
                     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │    File Processor      │
                     │(app/services/file_proc)│
                     └───────┬────────┬───────┘
                             │        │
             ┌───────────────┘        └────────────────┐
             ▼                                         ▼
  ┌──────────────────────┐                  ┌─────────────────────┐
  │  Shapefile Unzipper  │                  │  KML XML Parser     │
  │  & GeoPandas Reader  │                  │ (app/services/kml)  │
  └──────────┬───────────┘                  └──────────┬──────────┘
             │                                         │
             └───────────────────┬─────────────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │  CRS Transformer       │
                     │ (Auto UTM Estimation)  │
                     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │   Measurement Engine   │
                     │  (Polygon Area, Line)  │
                     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │    Thread-Safe Store   │
                     │(app/storage/file_store)│
                     └────────────────────────┘
```

### Application Structure
```
geospatial-measurement-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instance, CORS & exception handling
│   ├── config.py            # Paths, limits, allowed extensions
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py        # REST API endpoints
│   │   └── models.py        # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── file_processor.py # File reader & orchestrator
│   │   ├── crs_transformer.py# CRS detection & Auto-UTM projection
│   │   ├── kml_parser.py    # Robust XML KML fallback parser
│   │   └── measurement_engine.py # Area, length calculation logic
│   └── storage/
│       ├── __init__.py
│       └── file_store.py    # Thread-safe metadata & JSON persistence
├── tests/
│   ├── test_api.py          # API route integration tests
│   ├── test_processor.py    # CRS, KML, and measurement unit tests
│   └── sample_data/         # KML & Shapefile test files
├── requirements.txt
├── README.md
└── run.py
```

---

## 🌐 CRS Handling Strategy

### Problem Statement
Geographic coordinate reference systems such as **EPSG:4326** measure coordinates in angular degrees ($\text{longitude}, \text{latitude}$). Calculating area or distance directly on angular degrees yields meaningless values ($deg^2$ or spherical arc degrees).

### Solution: Dynamic Universal Transverse Mercator (UTM) Auto-Projection
To guarantee metric spatial accuracy ($m$ and $m^2$):
1. **Centroid Extraction**: The application computes the centroid of each feature or feature dataset $(\lambda, \phi)$.
2. **UTM Zone Calculation**:
   $$\text{Zone} = \left\lfloor \frac{\lambda + 180}{6} \right\rfloor + 1$$
   - Northern Hemisphere ($\phi \ge 0$): $\text{EPSG Code} = 32600 + \text{Zone}$
   - Southern Hemisphere ($\phi < 0$): $\text{EPSG Code} = 32700 + \text{Zone}$
3. **Rigorous Reprojection**: Shapely geometries are transformed from the source CRS (`EPSG:4326`) to the target UTM projected coordinate system using `pyproj.Transformer.from_crs(..., always_xy=True)`.
4. **Metric Calculation**: Area and length are calculated on planar projected geometries.

---

## 💡 Key Design Decisions & Alternatives Considered

1. **FastAPI vs. Django**:
   - *Chosen*: **FastAPI**.
   - *Rationale*: FastAPI provides lightweight overhead, native async file stream handling, automatic OpenAPI/Swagger documentation generation, and seamless integration with Pydantic v2 validation models.

2. **Dual-Layer KML Parsing**:
   - *Chosen*: GeoPandas with fallback to custom `xml.etree.ElementTree` parser (`KMLParser`).
   - *Rationale*: System GDAL drivers on some OS environments (e.g. Windows without compiled `LIBKML` binaries) fail to read KML via GeoPandas/Fiona. The built-in XML parser ensures 100% platform portability with zero native binary dependencies.

3. **Graceful Error Handling for Unsupported Geometries**:
   - *Chosen*: `MeasurementEngine` safe dispatch with `shapely.validation.make_valid()`.
   - *Rationale*: Malformed or invalid geometries (e.g. self-intersecting polygons or `GeometryCollection` containing points and lines) do not crash the service. Point features return `"measurement_type": "none"`, and invalid shapes are repaired automatically before measurement.

---

## 🎓 Learnings & Future Scope

### Learnings
- **Coordinate Reference Systems**: Understanding the mathematical difference between geodetic spheroidal coordinates (WGS84) and conformal planar map projections (UTM).
- **Multi-Driver Parsing**: Handling edge cases in Shapefile zip archives (ensuring `.shx` and `.dbf` sidecars exist) and parsing KML XML namespaces.

### Future Scope & Roadmap
1. **PostGIS / SpatiaLite Integration**: Transition from JSON file storage to a spatial database like PostGIS for spatial index querying (`ST_Area`, `ST_Length`).
2. **GeoJSON Export Endpoint**: Provide `GET /api/files/{id}/geojson` to stream feature geometries directly to frontend map clients (Mapbox GL JS, Leaflet, OpenLayers).
3. **Async Background Workers**: Offload processing of massive shapefiles (>100,000 features) to Celery or Redis Queue tasks with WebSocket progress updates.
4. **Cloud Object Storage**: Store uploaded raw files in AWS S3 or Google Cloud Storage buckets.
