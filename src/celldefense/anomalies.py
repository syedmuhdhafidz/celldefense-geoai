"""Synthetic suspicious-scenario injection."""

from collections.abc import Sequence
from math import ceil, floor

import numpy as np
import pandas as pd

from celldefense.config import DEFAULT_RANDOM_SEED
from celldefense.network import (
    BaseStation,
    SYNTHETIC_BASE_STATIONS,
)
from celldefense.radio import derive_nominal_quality
from celldefense.schema import validate_observations


def _find_station(
    stations: Sequence[BaseStation],
    cell_id: str,
) -> BaseStation:
    matching_stations = [
        station
        for station in stations
        if station.cell_id == cell_id
    ]

    if not matching_stations:
        raise ValueError(
            f"Unknown cloned cell_id: {cell_id}"
        )

    return matching_stations[0]


def inject_cloned_cell(
    observations: pd.DataFrame,
    route_id: str = "route-west-east",
    cloned_cell_id: str = "cell-001",
    start_fraction: float = 0.55,
    end_fraction: float = 0.70,
    stations: Sequence[
        BaseStation
    ] = SYNTHETIC_BASE_STATIONS,
    random_seed: int = DEFAULT_RANDOM_SEED + 1,
) -> pd.DataFrame:
    """Inject a geographically inconsistent cloned-cell signature."""

    validate_observations(observations)

    if not 0.0 <= start_fraction < end_fraction <= 1.0:
        raise ValueError(
            "Fractions must satisfy "
            "0 <= start_fraction < end_fraction <= 1."
        )

    route_rows = observations.loc[
        observations["route_id"] == route_id
    ].sort_values("timestamp")

    if route_rows.empty:
        raise ValueError(
            f"Unknown or empty route_id: {route_id}"
        )

    cloned_station = _find_station(
        stations=stations,
        cell_id=cloned_cell_id,
    )

    route_indices = route_rows.index.to_list()
    start_position = floor(
        len(route_indices) * start_fraction
    )
    end_position = ceil(
        len(route_indices) * end_fraction
    )

    anomaly_indices = route_indices[
        start_position:end_position
    ]

    if not anomaly_indices:
        raise ValueError(
            "The selected anomaly window contains no observations."
        )

    result = observations.copy(deep=True)
    random_generator = np.random.default_rng(
        random_seed
    )

    anomaly_count = len(anomaly_indices)
    anomalous_rsrp = np.clip(
        random_generator.normal(
            loc=-58.0,
            scale=1.5,
            size=anomaly_count,
        ),
        -65.0,
        -50.0,
    )

    anomalous_rsrq: list[float] = []
    anomalous_sinr: list[float] = []

    for rsrp_dbm in anomalous_rsrp:
        nominal_rsrq, nominal_sinr = (
            derive_nominal_quality(
                float(rsrp_dbm)
            )
        )

        anomalous_rsrq.append(
            float(
                np.clip(
                    nominal_rsrq
                    + random_generator.normal(
                        loc=0.0,
                        scale=0.5,
                    ),
                    -40.0,
                    0.0,
                )
            )
        )
        anomalous_sinr.append(
            float(
                np.clip(
                    nominal_sinr
                    + random_generator.normal(
                        loc=0.0,
                        scale=1.0,
                    ),
                    -30.0,
                    50.0,
                )
            )
        )

    result.loc[
        anomaly_indices,
        "operator_id",
    ] = cloned_station.operator_id
    result.loc[
        anomaly_indices,
        "rat",
    ] = cloned_station.rat
    result.loc[
        anomaly_indices,
        "cell_id",
    ] = cloned_station.cell_id
    result.loc[
        anomaly_indices,
        "pci",
    ] = cloned_station.pci
    result.loc[
        anomaly_indices,
        "tac",
    ] = cloned_station.tac
    result.loc[
        anomaly_indices,
        "arfcn",
    ] = cloned_station.arfcn
    result.loc[
        anomaly_indices,
        "rsrp_dbm",
    ] = np.round(anomalous_rsrp, 2)
    result.loc[
        anomaly_indices,
        "rsrq_db",
    ] = np.round(anomalous_rsrq, 2)
    result.loc[
        anomaly_indices,
        "sinr_db",
    ] = np.round(anomalous_sinr, 2)
    result.loc[
        anomaly_indices,
        "neighbour_count",
    ] = 1
    result.loc[
        anomaly_indices,
        "handover_event",
    ] = False
    result.loc[
        anomaly_indices,
        "scenario",
    ] = "cloned_cell"
    result.loc[
        anomaly_indices,
        "is_anomaly",
    ] = True

    first_anomaly_index = anomaly_indices[0]
    result.loc[
        first_anomaly_index,
        "handover_event",
    ] = True

    if end_position < len(route_indices):
        first_post_anomaly_index = route_indices[
            end_position
        ]
        result.loc[
            first_post_anomaly_index,
            "handover_event",
        ] = True

    validate_observations(result)

    return result