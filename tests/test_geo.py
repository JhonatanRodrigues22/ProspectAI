import pytest

from backend.app.domain import GeoPoint
from backend.app.domain.geo import haversine_distance_km


def test_haversine_distance_between_known_points() -> None:
    sao_paulo = GeoPoint(latitude=-23.55052, longitude=-46.633308)
    campinas = GeoPoint(latitude=-22.90556, longitude=-47.06083)

    distance = haversine_distance_km(sao_paulo, campinas)

    assert distance == pytest.approx(84.3, abs=1)


def test_haversine_distance_to_same_point_is_zero() -> None:
    point = GeoPoint(latitude=-23.55052, longitude=-46.633308)

    assert haversine_distance_km(point, point) == pytest.approx(0)
