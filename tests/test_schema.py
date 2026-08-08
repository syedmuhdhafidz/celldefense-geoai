import pandas as pd
import pytest

from celldefense.schema import (
    ObservationValidationError,
    validate_observations,
)


def make_valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "observation_id": "obs-000001",
                "timestamp": "2026-08-08T08:00:00+08:00",
                "latitude": 2.9225,
                "longitude": 101.6550,
                "route_id": "route-01",
                "sensor_id": "sensor-01",
                "operator_id": "OP_A",
                "rat": "LTE",
                "cell_id": "cell-001",
                "pci": 101,
                "tac": 5001,
                "arfcn": 1650,
                "rsrp_dbm": -84.5,
                "rsrq_db": -10.2,
                "sinr_db": 18.0,
                "neighbour_count": 5,
                "handover_event": False,
                "scenario": "baseline",
                "is_anomaly": False,
            }
        ]
    )


def test_valid_observations_are_accepted() -> None:
    frame = make_valid_frame()

    validate_observations(frame)


def test_missing_column_is_rejected() -> None:
    frame = make_valid_frame().drop(columns=["rsrp_dbm"])

    with pytest.raises(
        ObservationValidationError,
        match="Missing required columns",
    ):
        validate_observations(frame)


def test_invalid_signal_strength_is_rejected() -> None:
    frame = make_valid_frame()
    frame.loc[0, "rsrp_dbm"] = -250.0

    with pytest.raises(
        ObservationValidationError,
        match="rsrp_dbm column must be between",
    ):
        validate_observations(frame)


def test_sensitive_identifier_is_rejected() -> None:
    frame = make_valid_frame()
    frame["imsi"] = "not-allowed"

    with pytest.raises(
        ObservationValidationError,
        match="Forbidden sensitive columns",
    ):
        validate_observations(frame)