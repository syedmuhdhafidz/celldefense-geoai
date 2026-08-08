"""Supporting access-route planning for investigation areas."""

from collections.abc import Sequence

import geopandas as gpd
import pandas as pd
from shapely.geometry import (
    LineString,
    Point,
)
from shapely.ops import substring

from celldefense.clustering import (
    CYBERJAYA_PROJECTED_CRS,
    GEOGRAPHIC_CRS,
)
from celldefense.routes import (
    SYNTHETIC_ROUTES,
    Route,
)

RESPONSE_PLAN_COLUMNS = [
    "priority_rank",
    "cluster_id",
    "route_id",
    "staging_endpoint",
    "staging_latitude",
    "staging_longitude",
    "access_latitude",
    "access_longitude",
    "route_distance_m",
    "off_route_distance_m",
    "path_wkt",
]


def _to_projected(
    geometry: Point | LineString,
) -> Point | LineString:
    """Project a WGS 84 geometry into local metre coordinates."""

    return (
        gpd.GeoSeries(
            [geometry],
            crs=GEOGRAPHIC_CRS,
        )
        .to_crs(CYBERJAYA_PROJECTED_CRS)
        .iloc[0]
    )


def _to_geographic(
    geometry: Point | LineString,
) -> Point | LineString:
    """Project a local metre geometry back into WGS 84."""

    return (
        gpd.GeoSeries(
            [geometry],
            crs=CYBERJAYA_PROJECTED_CRS,
        )
        .to_crs(GEOGRAPHIC_CRS)
        .iloc[0]
    )


def _route_line(route: Route) -> LineString:
    """Create a WGS 84 line from route control points."""

    return LineString(
        [
            (longitude, latitude)
            for latitude, longitude
            in route.control_points
        ]
    )


def _ensure_line_string(
    geometry: Point | LineString,
) -> LineString:
    """Represent a zero-length substring as a valid line."""

    if isinstance(geometry, LineString):
        return geometry

    coordinate = geometry.coords[0]
    return LineString(
        [
            coordinate,
            coordinate,
        ]
    )


def plan_response_routes(
    cluster_summary: pd.DataFrame,
    routes: Sequence[Route] = SYNTHETIC_ROUTES,
) -> pd.DataFrame:
    """Plan a synthetic access route for each priority area."""

    required_columns = {
        "priority_rank",
        "cluster_id",
        "centroid_latitude",
        "centroid_longitude",
    }
    missing_columns = required_columns - set(
        cluster_summary.columns
    )
    if missing_columns:
        raise ValueError(
            "Missing response-planning columns: "
            f"{sorted(missing_columns)}"
        )

    if not routes:
        raise ValueError(
            "At least one response route is required."
        )

    if cluster_summary.empty:
        return pd.DataFrame(
            columns=RESPONSE_PLAN_COLUMNS
        )

    projected_routes: list[
        tuple[Route, LineString]
    ] = []

    for route in routes:
        geographic_line = _route_line(route)
        projected_line = _to_projected(
            geographic_line
        )

        if not isinstance(
            projected_line,
            LineString,
        ):
            raise TypeError(
                "Projected route must be a LineString."
            )

        projected_routes.append(
            (
                route,
                projected_line,
            )
        )

    response_plans: list[
        dict[str, object]
    ] = []

    for cluster in cluster_summary.itertuples():
        geographic_centroid = Point(
            cluster.centroid_longitude,
            cluster.centroid_latitude,
        )
        projected_centroid = _to_projected(
            geographic_centroid
        )

        if not isinstance(
            projected_centroid,
            Point,
        ):
            raise TypeError(
                "Projected centroid must be a Point."
            )

        route_candidates: list[
            dict[str, object]
        ] = []

        for route, projected_line in projected_routes:
            access_position = (
                projected_line.project(
                    projected_centroid
                )
            )
            projected_access_point = (
                projected_line.interpolate(
                    access_position
                )
            )
            off_route_distance = (
                projected_centroid.distance(
                    projected_access_point
                )
            )

            distance_from_start = access_position
            distance_from_end = (
                projected_line.length
                - access_position
            )

            if (
                distance_from_start
                <= distance_from_end
            ):
                staging_endpoint = "start"
                route_distance = distance_from_start
                projected_staging_point = (
                    projected_line.interpolate(0.0)
                )
                projected_path = substring(
                    projected_line,
                    0.0,
                    access_position,
                )
            else:
                staging_endpoint = "end"
                route_distance = distance_from_end
                projected_staging_point = (
                    projected_line.interpolate(
                        projected_line.length
                    )
                )
                projected_path = substring(
                    projected_line,
                    access_position,
                    projected_line.length,
                )

                path_coordinates = list(
                    projected_path.coords
                )
                path_coordinates.reverse()
                projected_path = LineString(
                    path_coordinates
                )

            route_candidates.append(
                {
                    "route": route,
                    "off_route_distance": (
                        off_route_distance
                    ),
                    "route_distance": route_distance,
                    "staging_endpoint": (
                        staging_endpoint
                    ),
                    "projected_staging_point": (
                        projected_staging_point
                    ),
                    "projected_access_point": (
                        projected_access_point
                    ),
                    "projected_path": (
                        _ensure_line_string(
                            projected_path
                        )
                    ),
                }
            )

        selected_route = min(
            route_candidates,
            key=lambda candidate: (
                candidate["off_route_distance"],
                candidate["route"].route_id,
            ),
        )

        staging_point = _to_geographic(
            selected_route[
                "projected_staging_point"
            ]
        )
        access_point = _to_geographic(
            selected_route[
                "projected_access_point"
            ]
        )
        response_path = _to_geographic(
            selected_route["projected_path"]
        )

        if not isinstance(staging_point, Point):
            raise TypeError(
                "Geographic staging point must be a Point."
            )
        if not isinstance(access_point, Point):
            raise TypeError(
                "Geographic access point must be a Point."
            )
        if not isinstance(
            response_path,
            LineString,
        ):
            raise TypeError(
                "Geographic response path must be "
                "a LineString."
            )

        selected_route_definition = (
            selected_route["route"]
        )

        response_plans.append(
            {
                "priority_rank": int(
                    cluster.priority_rank
                ),
                "cluster_id": int(
                    cluster.cluster_id
                ),
                "route_id": (
                    selected_route_definition.route_id
                ),
                "staging_endpoint": (
                    selected_route[
                        "staging_endpoint"
                    ]
                ),
                "staging_latitude": round(
                    float(staging_point.y),
                    6,
                ),
                "staging_longitude": round(
                    float(staging_point.x),
                    6,
                ),
                "access_latitude": round(
                    float(access_point.y),
                    6,
                ),
                "access_longitude": round(
                    float(access_point.x),
                    6,
                ),
                "route_distance_m": round(
                    float(
                        selected_route[
                            "route_distance"
                        ]
                    ),
                    2,
                ),
                "off_route_distance_m": round(
                    float(
                        selected_route[
                            "off_route_distance"
                        ]
                    ),
                    2,
                ),
                "path_wkt": response_path.wkt,
            }
        )

    response_plan = pd.DataFrame(
        response_plans,
        columns=RESPONSE_PLAN_COLUMNS,
    )

    return response_plan.sort_values(
        by="priority_rank",
        ignore_index=True,
    )