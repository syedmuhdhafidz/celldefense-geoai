"""Validation rules for CellDefense RF observations."""

from collections.abc import Iterable

import pandas as pd


REQUIRED_COLUMNS = [
    "observation_id",
    "timestamp",
    "latitude",
    "longitude",
    "route_id",
    "sensor_id",
    "operator_id",
    "rat",
    "cell_id",
    "pci",
    "tac",
    "arfcn",
    "rsrp_dbm",
    "rsrq_db",
    "sinr_db",
    "neighbour_count",
    "handover_event",
    "scenario",
    "is_anomaly",
]

FORBIDDEN_COLUMNS = {
    "imsi",
    "imei",
    "msisdn",
    "phone_number",
    "subscriber_id",
    "message_content",
}

ALLOWED_RATS = {
    "LTE",
    "NR",
}

ALLOWED_SCENARIOS = {
    "baseline",
    "legitimate_new_cell",
    "maintenance",
    "gps_error",
    "device_bias",
    "cloned_cell",
    "short_lived_cell",
    "handover_oscillation",
}

NUMERIC_RANGES = {
    "latitude": (-90.0, 90.0),
    "longitude": (-180.0, 180.0),
    "pci": (0, 1007),
    "tac": (0, 16_777_215),
    "arfcn": (0, 3_279_165),
    "rsrp_dbm": (-160.0, -30.0),
    "rsrq_db": (-40.0, 0.0),
    "sinr_db": (-30.0, 50.0),
    "neighbour_count": (0, 64),
}


class ObservationValidationError(ValueError):
    """Raised when an RF observation table violates the data contract."""


def _find_missing_columns(columns: Iterable[str]) -> list[str]:
    available = set(columns)
    return sorted(set(REQUIRED_COLUMNS) - available)


def _find_forbidden_columns(columns: Iterable[str]) -> list[str]:
    normalised = {column.lower() for column in columns}
    return sorted(FORBIDDEN_COLUMNS.intersection(normalised))


def validate_observations(frame: pd.DataFrame) -> None:
    """
    Validate an RF observation DataFrame.

    The function returns ``None`` when the data is valid and raises
    ``ObservationValidationError`` when a rule is violated.
    """

    if frame.empty:
        raise ObservationValidationError("Observation data must not be empty.")

    missing_columns = _find_missing_columns(frame.columns)
    if missing_columns:
        raise ObservationValidationError(
            f"Missing required columns: {missing_columns}"
        )

    forbidden_columns = _find_forbidden_columns(frame.columns)
    if forbidden_columns:
        raise ObservationValidationError(
            f"Forbidden sensitive columns detected: {forbidden_columns}"
        )

    parsed_timestamps = pd.to_datetime(
        frame["timestamp"],
        errors="coerce",
        utc=True,
    )
    if parsed_timestamps.isna().any():
        raise ObservationValidationError(
            "The timestamp column contains invalid values."
        )

    for column, (minimum, maximum) in NUMERIC_RANGES.items():
        numeric_values = pd.to_numeric(frame[column], errors="coerce")

        if numeric_values.isna().any():
            raise ObservationValidationError(
                f"The {column} column contains non-numeric values."
            )

        outside_range = ~numeric_values.between(minimum, maximum)
        if outside_range.any():
            raise ObservationValidationError(
                f"The {column} column must be between "
                f"{minimum} and {maximum}."
            )

    invalid_rats = sorted(set(frame["rat"]) - ALLOWED_RATS)
    if invalid_rats:
        raise ObservationValidationError(
            f"Unsupported RAT values: {invalid_rats}"
        )

    invalid_scenarios = sorted(
        set(frame["scenario"]) - ALLOWED_SCENARIOS
    )
    if invalid_scenarios:
        raise ObservationValidationError(
            f"Unsupported scenario values: {invalid_scenarios}"
        )

    for column in ("handover_event", "is_anomaly"):
        if not frame[column].isin([True, False]).all():
            raise ObservationValidationError(
                f"The {column} column must contain only Boolean values."
            )

    if frame["observation_id"].duplicated().any():
        raise ObservationValidationError(
            "The observation_id column must contain unique values."
        )