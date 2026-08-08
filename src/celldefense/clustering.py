"""Spatial corroboration and alert-cluster summarisation."""

import geopandas as gpd
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN


GEOGRAPHIC_CRS = "EPSG:4326"
CYBERJAYA_PROJECTED_CRS = "EPSG:32647"

CLUSTER_SUMMARY_COLUMNS = [
    "cluster_id",
    "observation_count",
    "start_time",
    "end_time",
    "centroid_latitude",
    "centroid_longitude",
    "mean_threat_score",
    "maximum_threat_score",
    "dominant_cell_id",
    "dominant_scenario",
    "true_anomaly_fraction",
]


def cluster_alerts(
    scored_observations: pd.DataFrame,
    maximum_distance_metres: float = 200.0,
    maximum_time_gap_seconds: float = 120.0,
    minimum_observations: int = 5,
) -> pd.DataFrame:
    """Assign cell-aware spatio-temporal alert clusters."""

    required_columns = {
        "timestamp",
        "latitude",
        "longitude",
        "cell_id",
        "predicted_anomaly",
    }
    missing_columns = required_columns - set(
        scored_observations.columns
    )
    if missing_columns:
        raise ValueError(
            f"Missing clustering columns: "
            f"{sorted(missing_columns)}"
        )

    if maximum_distance_metres <= 0:
        raise ValueError(
            "maximum_distance_metres must be positive."
        )

    if maximum_time_gap_seconds <= 0:
        raise ValueError(
            "maximum_time_gap_seconds must be positive."
        )

    if minimum_observations < 2:
        raise ValueError(
            "minimum_observations must be at least 2."
        )

    result = scored_observations.copy(deep=True)
    result["cluster_id"] = -1

    alert_mask = result[
        "predicted_anomaly"
    ].astype(bool)
    alert_rows = result.loc[alert_mask]

    if alert_rows.empty:
        return result

    next_cluster_id = 0

    for _, cell_alerts in alert_rows.groupby(
        "cell_id",
        sort=True,
        dropna=False,
    ):
        alert_geodata = gpd.GeoDataFrame(
            cell_alerts[
                [
                    "latitude",
                    "longitude",
                ]
            ].copy(),
            geometry=gpd.points_from_xy(
                cell_alerts["longitude"],
                cell_alerts["latitude"],
            ),
            crs=GEOGRAPHIC_CRS,
        ).to_crs(CYBERJAYA_PROJECTED_CRS)

        coordinates = np.column_stack(
            (
                alert_geodata.geometry.x,
                alert_geodata.geometry.y,
            )
        )

        timestamps = pd.to_datetime(
            cell_alerts["timestamp"],
            utc=True,
        )
        timestamp_seconds = (
            (
                timestamps - timestamps.min()
            )
            .dt.total_seconds()
            .to_numpy(dtype=float)
        )

        coordinate_differences = (
            coordinates[:, np.newaxis, :]
            - coordinates[np.newaxis, :, :]
        )
        spatial_distances = np.sqrt(
            np.sum(
                coordinate_differences**2,
                axis=2,
            )
        )
        temporal_distances = np.abs(
            timestamp_seconds[:, np.newaxis]
            - timestamp_seconds[np.newaxis, :]
        )

        normalised_distances = np.maximum(
            (
                spatial_distances
                / maximum_distance_metres
            ),
            (
                temporal_distances
                / maximum_time_gap_seconds
            ),
        )

        local_labels = DBSCAN(
            eps=1.0,
            min_samples=minimum_observations,
            metric="precomputed",
        ).fit_predict(normalised_distances)

        global_labels = np.full(
            shape=len(local_labels),
            fill_value=-1,
            dtype=int,
        )

        local_cluster_ids = sorted(
            cluster_id
            for cluster_id in np.unique(
                local_labels
            )
            if cluster_id >= 0
        )

        for local_cluster_id in local_cluster_ids:
            cluster_mask = (
                local_labels == local_cluster_id
            )
            global_labels[
                cluster_mask
            ] = next_cluster_id
            next_cluster_id += 1

        result.loc[
            cell_alerts.index,
            "cluster_id",
        ] = global_labels

    return result


def summarise_alert_clusters(
    clustered_observations: pd.DataFrame,
) -> pd.DataFrame:
    """Create one operational summary row per spatial cluster."""

    required_columns = {
        "cluster_id",
        "timestamp",
        "latitude",
        "longitude",
        "threat_score",
        "cell_id",
        "scenario",
        "is_anomaly",
    }
    missing_columns = required_columns - set(
        clustered_observations.columns
    )
    if missing_columns:
        raise ValueError(
            f"Missing summary columns: "
            f"{sorted(missing_columns)}"
        )

    confirmed_clusters = clustered_observations.loc[
        clustered_observations["cluster_id"] >= 0
    ].copy()

    if confirmed_clusters.empty:
        return pd.DataFrame(
            columns=CLUSTER_SUMMARY_COLUMNS
        )

    confirmed_clusters["timestamp"] = pd.to_datetime(
        confirmed_clusters["timestamp"],
        utc=True,
    )

    summaries: list[dict[str, object]] = []

    for cluster_id, cluster_data in (
        confirmed_clusters.groupby(
            "cluster_id",
            sort=True,
        )
    ):
        dominant_cell_id = (
            cluster_data["cell_id"]
            .mode()
            .iloc[0]
        )
        dominant_scenario = (
            cluster_data["scenario"]
            .mode()
            .iloc[0]
        )

        summaries.append(
            {
                "cluster_id": int(cluster_id),
                "observation_count": len(
                    cluster_data
                ),
                "start_time": cluster_data[
                    "timestamp"
                ].min(),
                "end_time": cluster_data[
                    "timestamp"
                ].max(),
                "centroid_latitude": round(
                    float(
                        cluster_data[
                            "latitude"
                        ].mean()
                    ),
                    6,
                ),
                "centroid_longitude": round(
                    float(
                        cluster_data[
                            "longitude"
                        ].mean()
                    ),
                    6,
                ),
                "mean_threat_score": round(
                    float(
                        cluster_data[
                            "threat_score"
                        ].mean()
                    ),
                    2,
                ),
                "maximum_threat_score": round(
                    float(
                        cluster_data[
                            "threat_score"
                        ].max()
                    ),
                    2,
                ),
                "dominant_cell_id": (
                    dominant_cell_id
                ),
                "dominant_scenario": (
                    dominant_scenario
                ),
                "true_anomaly_fraction": round(
                    float(
                        cluster_data[
                            "is_anomaly"
                        ].astype(float).mean()
                    ),
                    4,
                ),
            }
        )

    summary = pd.DataFrame(
        summaries,
        columns=CLUSTER_SUMMARY_COLUMNS,
    )

    return summary.sort_values(
        by=[
            "maximum_threat_score",
            "observation_count",
        ],
        ascending=[False, False],
        ignore_index=True,
    )