"""Deterministic drive routes for the synthetic RF dataset."""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from shapely.geometry import LineString

from celldefense.config import AreaOfInterest, CYBERJAYA_AOI


Coordinate = tuple[float, float]


@dataclass(frozen=True, slots=True)
class Route:
    """A simulated drive route defined by latitude-longitude control points."""

    route_id: str
    control_points: tuple[Coordinate, ...]

    def __post_init__(self) -> None:
        if len(self.control_points) < 2:
            raise ValueError(
                "A route must contain at least two control points."
            )


SYNTHETIC_ROUTES = (
    Route(
        route_id="route-north-south",
        control_points=(
            (2.8950, 101.6500),
            (2.9150, 101.6480),
            (2.9350, 101.6550),
            (2.9600, 101.6620),
        ),
    ),
    Route(
        route_id="route-west-east",
        control_points=(
            (2.9100, 101.6250),
            (2.9150, 101.6450),
            (2.9200, 101.6650),
            (2.9250, 101.6950),
        ),
    ),
    Route(
        route_id="route-northern-loop",
        control_points=(
            (2.9500, 101.6250),
            (2.9450, 101.6450),
            (2.9400, 101.6700),
            (2.9500, 101.6950),
            (2.9650, 101.6800),
        ),
    ),
)


def validate_routes(
    routes: Sequence[Route],
    area_of_interest: AreaOfInterest = CYBERJAYA_AOI,
) -> None:
    """Validate route identifiers and geographic control points."""

    if not routes:
        raise ValueError("At least one route is required.")

    route_ids = [route.route_id for route in routes]
    if len(route_ids) != len(set(route_ids)):
        raise ValueError("Route identifiers must be unique.")

    outside_points: list[str] = []

    for route in routes:
        for point_number, (latitude, longitude) in enumerate(
            route.control_points,
            start=1,
        ):
            if not area_of_interest.contains(latitude, longitude):
                outside_points.append(
                    f"{route.route_id}:point-{point_number}"
                )

    if outside_points:
        raise ValueError(
            f"Route points outside the pilot area: {outside_points}"
        )


def sample_route(
    route: Route,
    sample_count: int,
) -> pd.DataFrame:
    """Create evenly spaced observation coordinates along a route."""

    if sample_count < 2:
        raise ValueError("sample_count must be at least 2.")

    line = LineString(
        [
            (longitude, latitude)
            for latitude, longitude in route.control_points
        ]
    )

    fractions = np.linspace(
        start=0.0,
        stop=1.0,
        num=sample_count,
    )
    sampled_points = [
        line.interpolate(float(fraction), normalized=True)
        for fraction in fractions
    ]

    return pd.DataFrame(
        {
            "sample_index": np.arange(sample_count),
            "route_id": route.route_id,
            "latitude": [
                point.y for point in sampled_points
            ],
            "longitude": [
                point.x for point in sampled_points
            ],
        }
    )