# Geospatial File Measurement API

A FastAPI backend service that accepts geospatial files (Shapefile `.zip` packages and `.kml` files), extracts feature geometries and attributes, handles coordinate reference system (CRS) transformations automatically, and returns calculated measurements (Area for Polygons, Length for LineStrings).

---

## 📌 Features & Minimum Requirements Met

- **Backend Framework**: Built with **FastAPI**, **GeoPandas**, **Shapely**, and **PyProj**.
- **File Upload**: `POST /api/files/` accepts `.zip` shapefiles and `.kml` vector files.
- **Geospatial Processing**: Reads features and extracts Feature ID, Geometry type, Geometry coordinates, CRS, and Properties/Attributes.
- **Graceful Error Handling**: Unsupported or invalid geometries are handled gracefully without application crashes.
- **Measurements**:
  - **Polygon**: Area calculated in square meters ($m^2$) and square kilometers ($km^2$).
  - **LineString**: Length calculated in meters ($m$) and kilometers ($km$).
  - **Point**: Handled cleanly with no measurement required (`"measurement_type": "none"`).
- **CRS Handling & Auto-UTM Projection**: Geographic coordinates (`EPSG:4326` in lat/lon degrees) are dynamically transformed to an appropriate local projected coordinate system (**Universal Transverse Mercator / UTM zone**) based on feature centroids before measuring area or length in SI metric units.

---

## 🛠️ Setup & Running Locally

### Prerequisites
- Python 3.10 or higher
- `pip`

### 1. Clone Repository
```bash
git clone https://github.com/SAIKUMAR1521/geospatial-measurement-api.git
cd geospatial-measurement-api
```

### 2. Create and Activate Virtual Environment
```bash
# On Windows:
python -m venv .venv
.venv\Scripts\activate

# On Linux / macOS:
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Start Server
```bash
python run.py
```
The API server will run at `http://127.0.0.1:8000`.

Interactive Swagger API docs: **`http://127.0.0.1:8000/docs`**

---

## 🧪 Running Tests

Run the unit and integration test suite using `pytest`:

```bash
pytest -v
```

---

## 🔌 API Endpoints & Examples

### 1. Upload & Process File
`POST /api/files/`
- **Request**: `multipart/form-data` with `file` (.zip or .kml)
- **Response (`201 Created`)**:
```json
{
  "id": "a1b2c3d4",
  "filename": "survey.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "created_at": "2026-10-07T21:15:00Z",
  "error_message": null
}
```

### 2. Get File Information
`GET /api/files/{id}/`
- **Response (`200 OK`)**:
```json
{
  "id": "a1b2c3d4",
  "filename": "survey.kml",
  "feature_count": 3,
  "crs": "EPSG:4326",
  "status": "COMPLETED",
  "created_at": "2026-10-07T21:15:00Z"
}
```

### 3. Get Feature Measurements
`GET /api/files/{id}/measurements/`
- **Response (`200 OK`)**:
```json
{
  "file_id": "a1b2c3d4",
  "filename": "survey.kml",
  "status": "COMPLETED",
  "total_features": 3,
  "summary": {
    "total_area_sq_m": 250000.5,
    "total_area_sq_km": 0.25,
    "total_length_m": 1500.75,
    "total_length_km": 1.5,
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
      "value_sq_km": 0.25,
      "value_m": null,
      "value_km": null,
      "formatted": "250,000.50 m² (0.2500 km²)",
      "properties": {
        "name": "Survey Zone A",
        "Owner": "Acme Corp"
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
      "value_km": 1.5,
      "formatted": "1,500.75 m (1.5008 km)",
      "properties": {
        "name": "Access Road"
      },
      "geometry_summary": "Centroid: (77.5925, 12.9725)"
    },
    {
      "feature_id": "Control Point",
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
        "name": "Control Point"
      },
      "geometry_summary": "Location: (77.5925, 12.9725)"
    }
  ]
}
```

### 4. List Uploaded Files
`GET /api/files/`

### 5. Delete File
`DELETE /api/files/{id}/`

---

## 🏛️ Application Architecture & Flows

### Project Structure
```
geospatial-measurement-api/
├── app/
│   ├── main.py              # FastAPI app instance & CORS
│   ├── config.py            # Paths, storage, file limits
│   ├── api/
│   │   ├── routes.py        # REST API endpoints
│   │   └── models.py        # Pydantic data schemas
│   ├── services/
│   │   ├── file_processor.py # Reads Shapefile zip & KML, orchestrates pipeline
│   │   ├── crs_transformer.py# CRS detection & Auto-UTM estimation
│   │   ├── kml_parser.py    # Fallback XML KML feature parser
│   │   └── measurement_engine.py # Spatial measurement logic
│   └── storage/
│       └── file_store.py    # Thread-safe metadata & JSON storage manager
├── tests/
│   ├── test_api.py          # Route integration tests
│   ├── test_processor.py    # Unit tests for CRS, KML, and measurement calculations
│   └── sample_data/         # KML & Shapefile test files
├── requirements.txt
├── README.md
└── run.py
```

### File Processing Flow
1. **Upload & Storage**: The uploaded file (`.zip` or `.kml`) is saved to `data_storage/uploads/` with a unique ID.
2. **Extraction & Parsing**:
   - If `.zip`: Unzipped into a temp folder; shapefile components (`.shp`, `.shx`, `.dbf`) are loaded via GeoPandas.
   - If `.kml`: Parsed using GeoPandas, with fallback to `xml.etree.ElementTree` parsing for environment portability.
3. **CRS Transformation**: Original CRS is identified (defaulting to `EPSG:4326` if missing).
4. **Measurement Calculation**: Geometries are reprojected and processed by `MeasurementEngine`.
5. **Persistence**: Extracted metadata and feature measurements are saved into JSON storage.

---

## 🗺️ CRS Handling Strategy

### Problem
Geographic coordinate reference systems like `EPSG:4326` (WGS84) store coordinates in angular degrees ($\text{longitude}, \text{latitude}$). Directly calculating area or distance on degrees yields distorted, unphysical values ($deg^2$).

### Solution: Dynamic Auto-UTM Projection
To measure accurate metric values ($m$ and $m^2$):
1. **Centroid Extraction**: Calculate the centroid $(\text{lon}, \text{lat})$ of the geometry/dataset.
2. **UTM Zone Calculation**:
   $$\text{Zone} = \left\lfloor \frac{\text{lon} + 180}{6} \right\rfloor + 1$$
   - Northern Hemisphere ($\text{lat} \ge 0$): $\text{EPSG Code} = 32600 + \text{Zone}$
   - Southern Hemisphere ($\text{lat} < 0$): $\text{EPSG Code} = 32700 + \text{Zone}$
3. **Reprojection**: Geometries are transformed from `EPSG:4326` to the calculated UTM zone using `pyproj.Transformer`.
4. **Measurement**: Area and length are computed on the projected Cartesian plane.

---

## 💭 Technical Design Decisions

1. **FastAPI Framework**:
   Chosen over Django for minimal overhead, asynchronous file upload handling, built-in Pydantic v2 type safety, and automatic OpenAPI documentation generation.

2. **Dual-Layer KML Parsing**:
   GeoPandas relies on Fiona/GDAL drivers, which may lack native KML driver support on certain operating system environments. Implementing a secondary XML parser (`KMLParser`) using standard `xml.etree.ElementTree` guarantees that KML files are parsed reliably anywhere without native dependency issues.

3. **Graceful Geometry Validation**:
   Inputs from real-world shapefiles often contain self-intersecting polygons or mixed geometry types. Using `shapely.validation.make_valid()` ensures invalid polygons are repaired automatically rather than throwing unhandled exceptions.

---

## 📚 Learnings & Future Scope

### Learnings
- Working with geospatial coordinate transformations (Geodetic spherical coordinates vs. Conformal planar projections).
- Handling shapefile package dependencies (`.shp`, `.shx`, `.dbf`, `.prj`) and XML KML structure parsing.

### Future Scope
- **PostGIS Spatial Database**: Replace JSON storage with PostGIS for spatial index querying (`ST_Area`, `ST_Length`).
- **GeoJSON Output**: Add `GET /api/files/{id}/geojson` endpoint to directly serve GeoJSON for frontend web mapping libraries (Leaflet, Mapbox).
- **Asynchronous Task Queue**: Use Celery / Redis Queue for background processing of large shapefiles (>100,000 features).
