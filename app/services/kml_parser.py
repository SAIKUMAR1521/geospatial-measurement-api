import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, MultiLineString, MultiPoint, GeometryCollection
from shapely.geometry.base import BaseGeometry


class KMLParser:
    """Robust KML file parser using python's built-in xml.etree.ElementTree."""

    NAMESPACES = {
        "kml": "http://www.opengis.net/kml/2.2",
        "kml21": "http://earth.google.com/kml/2.1",
        "gx": "http://www.google.com/kml/ext/2.2"
    }

    @classmethod
    def parse_kml_file(cls, filepath: str) -> List[Dict[str, Any]]:
        tree = ET.parse(filepath)
        root = tree.getroot()
        
        features = []
        # Find all Placemark tags regardless of namespace
        placemarks = root.findall(".//{*}Placemark")
        
        for idx, placemark in enumerate(placemarks):
            feature_data = cls._parse_placemark(placemark, idx)
            if feature_data:
                features.append(feature_data)
                
        return features

    @classmethod
    def _parse_placemark(cls, placemark: ET.Element, index: int) -> Dict[str, Any]:
        properties = {}
        
        # Extract basic properties (name, description)
        name_node = placemark.find("./{*}name")
        if name_node is not None and name_node.text:
            properties["name"] = name_node.text.strip()
            
        desc_node = placemark.find("./{*}description")
        if desc_node is not None and desc_node.text:
            properties["description"] = desc_node.text.strip()

        # Extract ExtendedData / SimpleData
        for data in placemark.findall(".//{*}Data"):
            key = data.attrib.get("name")
            val_node = data.find("./{*}value")
            if key and val_node is not None and val_node.text:
                properties[key] = val_node.text.strip()

        for sdata in placemark.findall(".//{*}SimpleData"):
            key = sdata.attrib.get("name")
            if key and sdata.text:
                properties[key] = sdata.text.strip()

        # Parse geometry
        geom = cls._parse_geometry(placemark)
        if geom is None:
            return None

        feature_id = properties.get("name") or properties.get("id") or index

        return {
            "feature_id": feature_id,
            "geometry": geom,
            "geometry_type": geom.geom_type,
            "crs": "EPSG:4326",
            "properties": properties
        }

    @classmethod
    def _parse_geometry(cls, element: ET.Element) -> BaseGeometry:
        # Check Point
        pt_node = element.find(".//{*}Point")
        if pt_node is not None:
            return cls._parse_point(pt_node)

        # Check Polygon
        poly_node = element.find(".//{*}Polygon")
        if poly_node is not None:
            return cls._parse_polygon(poly_node)

        # Check LineString
        line_node = element.find(".//{*}LineString")
        if line_node is not None:
            return cls._parse_linestring(line_node)

        # Check MultiGeometry
        multi_node = element.find(".//{*}MultiGeometry")
        if multi_node is not None:
            return cls._parse_multigeometry(multi_node)

        return None

    @classmethod
    def _parse_coords(cls, coords_str: str) -> List[Tuple[float, float]]:
        coords = []
        if not coords_str:
            return coords
        
        # Coordinates in KML are space/newline separated tuples: "lon,lat,alt lon,lat,alt"
        raw_tuples = coords_str.strip().split()
        for raw_t in raw_tuples:
            parts = raw_t.split(",")
            if len(parts) >= 2:
                try:
                    lon = float(parts[0])
                    lat = float(parts[1])
                    coords.append((lon, lat))
                except ValueError:
                    continue
        return coords

    @classmethod
    def _parse_point(cls, node: ET.Element) -> Point:
        c_node = node.find("./{*}coordinates")
        if c_node is not None and c_node.text:
            coords = cls._parse_coords(c_node.text)
            if coords:
                return Point(coords[0])
        return None

    @classmethod
    def _parse_linestring(cls, node: ET.Element) -> LineString:
        c_node = node.find("./{*}coordinates")
        if c_node is not None and c_node.text:
            coords = cls._parse_coords(c_node.text)
            if len(coords) >= 2:
                return LineString(coords)
        return None

    @classmethod
    def _parse_polygon(cls, node: ET.Element) -> Polygon:
        outer_node = node.find(".//{*}outerBoundaryIs//{*}coordinates")
        if outer_node is None or not outer_node.text:
            return None

        outer_coords = cls._parse_coords(outer_node.text)
        if len(outer_coords) < 3:
            return None

        inner_holes = []
        for inner_node in node.findall(".//{*}innerBoundaryIs//{*}coordinates"):
            if inner_node.text:
                hole_coords = cls._parse_coords(inner_node.text)
                if len(hole_coords) >= 3:
                    inner_holes.append(hole_coords)

        return Polygon(shell=outer_coords, holes=inner_holes)

    @classmethod
    def _parse_multigeometry(cls, node: ET.Element) -> BaseGeometry:
        geoms = []
        for child in node:
            g = cls._parse_geometry(child)
            if g:
                geoms.append(g)

        if not geoms:
            return None

        # Check homogenous collection
        types = set(g.geom_type for g in geoms)
        if len(types) == 1:
            t = list(types)[0]
            if t == "Polygon":
                return MultiPolygon(geoms)
            elif t == "LineString":
                return MultiLineString(geoms)
            elif t == "Point":
                return MultiPoint(geoms)

        return GeometryCollection(geoms)
