import pytest

from celldefense.network import SYNTHETIC_BASE_STATIONS
from celldefense.radio import (
    derive_nominal_quality,
    expected_rsrp_dbm,
    haversine_distance_metres,
    select_serving_station,
)


def test_identical_coordinates_have_zero_distance() -> None:
    distance = haversine_distance_metres(
        latitude_1=2.9225,
        longitude_1=101.6550,
        latitude_2=2.9225,
        longitude_2=101.6550,
    )

    assert distance == pytest.approx(0.0)


def test_expected_signal_weakens_with_distance() -> None:
    station = SYNTHETIC_BASE_STATIONS[0]

    near_signal = expected_rsrp_dbm(
        station=station,
        sensor_latitude=station.latitude,
        sensor_longitude=station.longitude,
    )
    far_signal = expected_rsrp_dbm(
        station=station,
        sensor_latitude=station.latitude + 0.03,
        sensor_longitude=station.longitude + 0.03,
    )

    assert near_signal > far_signal


def test_nearby_station_is_selected_as_serving_station() -> None:
    expected_station = SYNTHETIC_BASE_STATIONS[2]

    estimate = select_serving_station(
        stations=SYNTHETIC_BASE_STATIONS,
        sensor_latitude=expected_station.latitude,
        sensor_longitude=expected_station.longitude,
    )

    assert estimate.station.cell_id == expected_station.cell_id


def test_nominal_quality_stays_inside_schema_ranges() -> None:
    rsrq_db, sinr_db = derive_nominal_quality(
        rsrp_dbm=-105.0,
    )

    assert -40.0 <= rsrq_db <= 0.0
    assert -30.0 <= sinr_db <= 50.0