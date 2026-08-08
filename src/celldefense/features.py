"""Feature engineering for CellDefense anomaly detection."""

from collections.abc import Sequence
from math import log1p

import pandas as pd

from celldefense.network import (
    BaseStation,
    SYNTHETIC_BASE_STATIONS,
)
from celldefense.radio import (
    expected_rsrp_dbm,
    haversine_distance_metres,
)
from celldefense.schema import validate_observations


UNKNOWN_CELL_DISTANCE_METRES = 20_000.0
UNKNOWN_CELL_EXPECTED_RSRP_DBM = -160.0

METADATA_COLUMNS = [
    "observation_id",
    "timestamp",
    "latitude",
    "longitude",
    "route_id",
    "sensor_id",
    "operator_id",
    "rat",
    "cell_id",
    "scenario",
    "is_anomaly",
]

MODEL_FEATURE_COLUMNS = [
    "neighbour_count",
    "handover_event_int",
    "known_cell",
    "rsrp_residual_db",
    "absolute_rsrp_residual_db",
    "signal_distance_inconsistency",
]


def build_feature_table(
    observations: pd.DataFrame,
    stations: Sequence[
        BaseStation
    ] = SYNTHETIC_BASE_STATIONS,
) -> pd.DataFrame:
    """Convert validated RF observations into model-ready features."""

    validate_observations(observations)

    station_lookup = {
        station.cell_id: station
        for station in stations
    }

    known_cell_values: list[int] = []
    distance_values: list[float] = []
    expected_rsrp_values: list[float] = []
    residual_values: list[float] = []
    inconsistency_values: list[float] = []

    for observation in observations.itertuples(
        index=False
    ):
        reported_station = station_lookup.get(
            observation.cell_id
        )

        if reported_station is None:
            known_cell = 0
            distance_metres = (
                UNKNOWN_CELL_DISTANCE_METRES
            )
            expected_signal = (
                UNKNOWN_CELL_EXPECTED_RSRP_DBM
            )
        else:
            known_cell = 1
            distance_metres = (
                haversine_distance_metres(
                    latitude_1=observation.latitude,
                    longitude_1=observation.longitude,
                    latitude_2=reported_station.latitude,
                    longitude_2=reported_station.longitude,
                )
            )
            expected_signal = expected_rsrp_dbm(
                station=reported_station,
                sensor_latitude=observation.latitude,
                sensor_longitude=observation.longitude,
            )

        residual = (
            float(observation.rsrp_dbm)
            - expected_signal
        )
        signal_distance_inconsistency = (
            max(residual, 0.0)
            * log1p(
                distance_metres / 1000.0
            )
        )

        known_cell_values.append(known_cell)
        distance_values.append(distance_metres)
        expected_rsrp_values.append(expected_signal)
        residual_values.append(residual)
        inconsistency_values.append(
            signal_distance_inconsistency
        )

    features = observations[
        METADATA_COLUMNS
    ].copy()

    features["rsrp_dbm"] = observations[
        "rsrp_dbm"
    ].astype(float)
    features["rsrq_db"] = observations[
        "rsrq_db"
    ].astype(float)
    features["sinr_db"] = observations[
        "sinr_db"
    ].astype(float)
    features["neighbour_count"] = observations[
        "neighbour_count"
    ].astype(int)
    features["handover_event_int"] = observations[
        "handover_event"
    ].astype(int)
    features["rat_is_nr"] = (
        observations["rat"] == "NR"
    ).astype(int)
    features["known_cell"] = known_cell_values
    features["distance_to_reported_cell_m"] = [
        round(value, 2)
        for value in distance_values
    ]
    features["expected_rsrp_dbm"] = [
        round(value, 2)
        for value in expected_rsrp_values
    ]
    features["rsrp_residual_db"] = [
        round(value, 2)
        for value in residual_values
    ]
    features["absolute_rsrp_residual_db"] = [
        round(abs(value), 2)
        for value in residual_values
    ]
    features["signal_distance_inconsistency"] = [
        round(value, 2)
        for value in inconsistency_values
    ]

    diagnostic_columns = [
        "rsrp_dbm",
        "distance_to_reported_cell_m",
        "expected_rsrp_dbm",
    ]

    return features[
        METADATA_COLUMNS
        + diagnostic_columns
        + MODEL_FEATURE_COLUMNS
    ]