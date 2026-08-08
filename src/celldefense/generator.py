"""Synthetic RF observation generation."""

from collections.abc import Sequence

import numpy as np
import pandas as pd

from celldefense.config import (
    DEFAULT_RANDOM_SEED,
    DEFAULT_SAMPLE_INTERVAL_SECONDS,
)
from celldefense.network import (
    BaseStation,
    SYNTHETIC_BASE_STATIONS,
    validate_network,
)
from celldefense.radio import (
    derive_nominal_quality,
    estimate_station_signals,
)
from celldefense.routes import (
    Route,
    SYNTHETIC_ROUTES,
    sample_route,
    validate_routes,
)
from celldefense.schema import (
    REQUIRED_COLUMNS,
    validate_observations,
)


DEFAULT_START_TIME = "2026-08-01T08:00:00+08:00"
DEFAULT_SAMPLES_PER_ROUTE = 600
ROUTE_START_GAP_MINUTES = 30
NEIGHBOUR_VISIBILITY_THRESHOLD_DBM = -125.0


def generate_baseline_observations(
    routes: Sequence[Route] = SYNTHETIC_ROUTES,
    stations: Sequence[BaseStation] = SYNTHETIC_BASE_STATIONS,
    samples_per_route: int = DEFAULT_SAMPLES_PER_ROUTE,
    start_time: str = DEFAULT_START_TIME,
    sample_interval_seconds: int = DEFAULT_SAMPLE_INTERVAL_SECONDS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> pd.DataFrame:
    """Generate deterministic baseline RF observations."""

    if samples_per_route < 2:
        raise ValueError(
            "samples_per_route must be at least 2."
        )

    if sample_interval_seconds < 1:
        raise ValueError(
            "sample_interval_seconds must be at least 1."
        )

    validate_routes(routes)
    validate_network(stations)

    start_timestamp = pd.Timestamp(start_time)
    if start_timestamp.tzinfo is None:
        raise ValueError(
            "start_time must include a timezone offset."
        )

    random_generator = np.random.default_rng(random_seed)
    records: list[dict[str, object]] = []
    observation_number = 1

    for route_number, route in enumerate(routes, start=1):
        route_points = sample_route(
            route=route,
            sample_count=samples_per_route,
        )

        route_start_time = start_timestamp + pd.Timedelta(
            minutes=(route_number - 1)
            * ROUTE_START_GAP_MINUTES
        )

        previous_cell_id: str | None = None
        sensor_id = f"sensor-{route_number:02d}"

        for point in route_points.itertuples(index=False):
            signal_estimates = estimate_station_signals(
                stations=stations,
                sensor_latitude=point.latitude,
                sensor_longitude=point.longitude,
            )

            serving_estimate = signal_estimates[0]
            serving_station = serving_estimate.station

            noisy_rsrp = serving_estimate.rsrp_dbm + float(
                random_generator.normal(
                    loc=0.0,
                    scale=2.0,
                )
            )
            bounded_rsrp = float(
                np.clip(noisy_rsrp, -160.0, -30.0)
            )

            nominal_rsrq, nominal_sinr = derive_nominal_quality(
                bounded_rsrp
            )

            noisy_rsrq = nominal_rsrq + float(
                random_generator.normal(
                    loc=0.0,
                    scale=1.0,
                )
            )
            noisy_sinr = nominal_sinr + float(
                random_generator.normal(
                    loc=0.0,
                    scale=2.0,
                )
            )

            bounded_rsrq = float(
                np.clip(noisy_rsrq, -40.0, 0.0)
            )
            bounded_sinr = float(
                np.clip(noisy_sinr, -30.0, 50.0)
            )

            neighbour_count = sum(
                estimate.rsrp_dbm
                >= NEIGHBOUR_VISIBILITY_THRESHOLD_DBM
                for estimate in signal_estimates[1:]
            )

            handover_event = (
                previous_cell_id is not None
                and serving_station.cell_id
                != previous_cell_id
            )

            timestamp = route_start_time + pd.Timedelta(
                seconds=(
                    point.sample_index
                    * sample_interval_seconds
                )
            )

            records.append(
                {
                    "observation_id": (
                        f"obs-{observation_number:07d}"
                    ),
                    "timestamp": timestamp,
                    "latitude": round(
                        float(point.latitude),
                        7,
                    ),
                    "longitude": round(
                        float(point.longitude),
                        7,
                    ),
                    "route_id": point.route_id,
                    "sensor_id": sensor_id,
                    "operator_id": (
                        serving_station.operator_id
                    ),
                    "rat": serving_station.rat,
                    "cell_id": serving_station.cell_id,
                    "pci": serving_station.pci,
                    "tac": serving_station.tac,
                    "arfcn": serving_station.arfcn,
                    "rsrp_dbm": round(bounded_rsrp, 2),
                    "rsrq_db": round(bounded_rsrq, 2),
                    "sinr_db": round(bounded_sinr, 2),
                    "neighbour_count": int(
                        neighbour_count
                    ),
                    "handover_event": bool(
                        handover_event
                    ),
                    "scenario": "baseline",
                    "is_anomaly": False,
                }
            )

            previous_cell_id = serving_station.cell_id
            observation_number += 1

    observations = pd.DataFrame(
        records,
        columns=REQUIRED_COLUMNS,
    )

    validate_observations(observations)

    return observations