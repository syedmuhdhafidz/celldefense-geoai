import pytest

from celldefense.config import CYBERJAYA_AOI
from celldefense.network import (
    BaseStation,
    SYNTHETIC_BASE_STATIONS,
    validate_network,
)


def test_synthetic_network_is_valid() -> None:
    validate_network(SYNTHETIC_BASE_STATIONS)


def test_synthetic_network_contains_lte_and_nr() -> None:
    technologies = {
        station.rat for station in SYNTHETIC_BASE_STATIONS
    }

    assert technologies == {"LTE", "NR"}


def test_all_synthetic_stations_are_inside_cyberjaya_aoi() -> None:
    assert all(
        CYBERJAYA_AOI.contains(
            station.latitude,
            station.longitude,
        )
        for station in SYNTHETIC_BASE_STATIONS
    )


def test_duplicate_cell_ids_are_rejected() -> None:
    duplicate_station = BaseStation(
        cell_id="cell-001",
        operator_id="OP_A",
        rat="LTE",
        pci=200,
        tac=5003,
        arfcn=1900,
        latitude=2.9300,
        longitude=101.6500,
        frequency_mhz=1800.0,
    )

    with pytest.raises(
        ValueError,
        match="cell_id values must be unique",
    ):
        validate_network(
            [
                SYNTHETIC_BASE_STATIONS[0],
                duplicate_station,
            ]
        )