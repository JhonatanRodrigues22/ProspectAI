from math import asin, cos, radians, sin, sqrt

from backend.app.domain.models import GeoPoint

EARTH_RADIUS_KM = 6371.0088


def haversine_distance_km(origin: GeoPoint, destination: GeoPoint) -> float:
    latitude_delta = radians(destination.latitude - origin.latitude)
    longitude_delta = radians(destination.longitude - origin.longitude)
    origin_latitude = radians(origin.latitude)
    destination_latitude = radians(destination.latitude)

    haversine = (
        sin(latitude_delta / 2) ** 2
        + cos(origin_latitude)
        * cos(destination_latitude)
        * sin(longitude_delta / 2) ** 2
    )
    angular_distance = 2 * asin(sqrt(min(1.0, haversine)))
    return EARTH_RADIUS_KM * angular_distance
