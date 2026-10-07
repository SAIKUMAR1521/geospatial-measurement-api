import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point
import zipfile
import tempfile
import os
from pathlib import Path

def create_shapefile_zip(output_path: str):
    # Create sample geometries in EPSG:4326
    poly = Polygon([(77.5900, 12.9700), (77.5950, 12.9700), (77.5950, 12.9750), (77.5900, 12.9750)])
    
    gdf = gpd.GeoDataFrame({
        'id': [1],
        'name': ['Test Parcel'],
        'geometry': [poly]
    }, crs="EPSG:4326")

    with tempfile.TemporaryDirectory() as tmpdir:
        shp_path = Path(tmpdir) / "test_polygon.shp"
        gdf.to_file(shp_path)

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                f = Path(tmpdir) / f"test_polygon{ext}"
                if f.exists():
                    zf.write(f, arcname=f.name)

if __name__ == "__main__":
    out = Path(__file__).parent / "sample_data" / "sample_shapefile.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    create_shapefile_zip(str(out))
    print(f"Created shapefile zip at {out}")
