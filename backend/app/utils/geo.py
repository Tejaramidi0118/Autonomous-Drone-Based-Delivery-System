from math import asin, cos, radians, sin, sqrt
from app.core import get_settings


settings = get_settings()


def is_in_hyderabad(lat: float, lng: float) -> bool:
    return (
        settings.hyderabad_min_lat <= lat <= settings.hyderabad_max_lat
        and settings.hyderabad_min_lng <= lng <= settings.hyderabad_max_lng
    )


def haversine_km(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    radius_km = 6371.0
    d_lat = radians(b_lat - a_lat)
    d_lng = radians(b_lng - a_lng)
    lat1 = radians(a_lat)
    lat2 = radians(b_lat)
    h = sin(d_lat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(d_lng / 2) ** 2
    return 2 * radius_km * asin(sqrt(h))


def linestring_wkt(points: list[list[float]]) -> str:
    return "LINESTRING(" + ", ".join(f"{lng} {lat}" for lat, lng in points) + ")"


def polygon_wkt(coords: list[list[float]]) -> str:
    closed = coords if coords[0] == coords[-1] else coords + [coords[0]]
    return "POLYGON((" + ", ".join(f"{lng} {lat}" for lat, lng in closed) + "))"


def point_wkt(lat: float, lng: float) -> str:
    return f"POINT({lng} {lat})"
