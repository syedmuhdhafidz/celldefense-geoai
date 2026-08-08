import pytest

from celldefense.config import CYBERJAYA_AOI
from celldefense.routes import (
    SYNTHETIC_ROUTES,
    sample_route,
    validate_routes,
)


def test_synthetic_routes_are_valid() -> None:
    validate_routes(SYNTHETIC_ROUTES)


def test_route_sampling_returns_requested_number_of_points() -> None:
    sampled_route = sample_route(
        route=SYNTHETIC_ROUTES[0],
        sample_count=600,
    )

    assert len(sampled_route) == 600
    assert list(sampled_route.columns) == [
        "sample_index",
        "route_id",
        "latitude",
        "longitude",
    ]


def test_sampled_points_remain_inside_cyberjaya_aoi() -> None:
    sampled_route = sample_route(
        route=SYNTHETIC_ROUTES[1],
        sample_count=600,
    )

    assert all(
        CYBERJAYA_AOI.contains(latitude, longitude)
        for latitude, longitude in zip(
            sampled_route["latitude"],
            sampled_route["longitude"],
            strict=True,
        )
    )


def test_route_sampling_rejects_too_few_points() -> None:
    with pytest.raises(
        ValueError,
        match="sample_count must be at least 2",
    ):
        sample_route(
            route=SYNTHETIC_ROUTES[0],
            sample_count=1,
        )