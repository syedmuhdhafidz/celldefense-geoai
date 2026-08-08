import pandas as pd
import pytest
from shapely import wkt
from shapely.geometry import LineString

from celldefense.routing import (
    RESPONSE_PLAN_COLUMNS,
    plan_response_routes,
)


def test_response_plan_selects_nearest_route() -> None:
    cluster_summary = pd.DataFrame(
        {
            "priority_rank": [1],
            "cluster_id": [0],
            "centroid_latitude": [2.920574],
            "centroid_longitude": [101.668516],
        }
    )

    response_plan = plan_response_routes(
        cluster_summary
    )

    assert len(response_plan) == 1

    plan = response_plan.iloc[0]

    assert plan["priority_rank"] == 1
    assert plan["cluster_id"] == 0
    assert plan["route_id"] == "route-west-east"
    assert plan["staging_endpoint"] in {
        "start",
        "end",
    }
    assert plan["route_distance_m"] > 0
    assert plan["off_route_distance_m"] < 50

    response_path = wkt.loads(
        plan["path_wkt"]
    )

    assert isinstance(
        response_path,
        LineString,
    )
    assert response_path.length > 0


def test_empty_summary_produces_empty_plan() -> None:
    empty_summary = pd.DataFrame(
        columns=[
            "priority_rank",
            "cluster_id",
            "centroid_latitude",
            "centroid_longitude",
        ]
    )

    response_plan = plan_response_routes(
        empty_summary
    )

    assert response_plan.empty
    assert (
        list(response_plan.columns)
        == RESPONSE_PLAN_COLUMNS
    )


def test_missing_planning_columns_are_rejected() -> None:
    incomplete_summary = pd.DataFrame(
        {
            "cluster_id": [0],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing response-planning columns",
    ):
        plan_response_routes(
            incomplete_summary
        )