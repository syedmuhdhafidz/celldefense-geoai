"""Simplified radio propagation utilities for synthetic observations."""

from collections.abc import Sequence
from dataclasses import dataclass
from math import asin, cos, log10, radians, sin, sqrt

from celldefense.network import BaseStation


EARTH_RADIUS_METRES = 6_371_008.8


@dataclass(frozen=True, slots=True)
class SignalEstimate:
    """Expected signal from one base station at one sensor location."""

    station: BaseStation
    distance_metres: float
    rsrp_dbm: float


def haversine_distance_metres(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """Calculate great-circle distance between two WGS 84 coordinates."""

    latitude_1_rad = radians(latitude_1)
    latitude_2_rad = radians(latitude_2)
    latitude_delta = radians(latitude_2 - latitude_1)
    longitude_delta = radians(longitude_2 - longitude_1)

    haversine_value = (
        sin(latitude_delta / 2.0) ** 2
        + cos(latitude_1_rad)
        * cos(latitude_2_rad)
        * sin(longitude_delta / 2.0) ** 2
    )

    angular_distance = 2.0 * asin(
        sqrt(min(1.0, haversine_value))
    )

    return EARTH_RADIUS_METRES * angular_distance


def expected_rsrp_dbm(
    station: BaseStation,
    sensor_latitude: float,
    sensor_longitude: float,
) -> float:
    """Estimate RSRP using a log-distance path-loss model."""

    distance_metres = haversine_distance_metres(
        latitude_1=station.latitude,
        longitude_1=station.longitude,
        latitude_2=sensor_latitude,
        longitude_2=sensor_longitude,
    )

    protected_distance = max(distance_metres, 1.0)

    return (
        station.reference_rsrp_at_1m_dbm
        - 10.0
        * station.path_loss_exponent
        * log10(protected_distance)
    )


def estimate_station_signals(
    stations: Sequence[BaseStation],
    sensor_latitude: float,
    sensor_longitude: float,
) -> tuple[SignalEstimate, ...]:
    """Estimate and rank station signals from strongest to weakest."""

    estimates = []

    for station in stations:
        distance_metres = haversine_distance_metres(
            latitude_1=station.latitude,
            longitude_1=station.longitude,
            latitude_2=sensor_latitude,
            longitude_2=sensor_longitude,
        )
        rsrp_dbm = expected_rsrp_dbm(
            station=station,
            sensor_latitude=sensor_latitude,
            sensor_longitude=sensor_longitude,
        )

        estimates.append(
            SignalEstimate(
                station=station,
                distance_metres=distance_metres,
                rsrp_dbm=rsrp_dbm,
            )
        )

    return tuple(
        sorted(
            estimates,
            key=lambda estimate: estimate.rsrp_dbm,
            reverse=True,
        )
    )


def select_serving_station(
    stations: Sequence[BaseStation],
    sensor_latitude: float,
    sensor_longitude: float,
) -> SignalEstimate:
    """Return the station with the strongest expected RSRP."""

    ranked_estimates = estimate_station_signals(
        stations=stations,
        sensor_latitude=sensor_latitude,
        sensor_longitude=sensor_longitude,
    )

    if not ranked_estimates:
        raise ValueError(
            "At least one base station is required."
        )

    return ranked_estimates[0]


def derive_nominal_quality(
    rsrp_dbm: float,
) -> tuple[float, float]:
    """Derive simplified nominal RSRQ and SINR values from RSRP."""

    signal_deficit = max(0.0, -80.0 - rsrp_dbm)

    rsrq_db = -8.0 - (0.30 * signal_deficit)
    sinr_db = 25.0 - (0.75 * signal_deficit)

    bounded_rsrq = max(-40.0, min(0.0, rsrq_db))
    bounded_sinr = max(-30.0, min(50.0, sinr_db))

    return bounded_rsrq, bounded_sinr