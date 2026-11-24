"""Great-circle distance, accurate enough to judge presence inside a branch radius."""
from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_METERS = 6_371_000.0


def distance_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = phi2 - phi1
    delta_lambda = radians(lng2 - lng1)
    haversine = sin(delta_phi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2) ** 2
    return 2 * EARTH_RADIUS_METERS * asin(sqrt(haversine))
