"""Cluster scored alerts into investigation areas."""

from pathlib import Path

import pandas as pd

from celldefense.clustering import (
    cluster_alerts,
    summarise_alert_clusters,
)


INPUT_PATH = (
    Path("data")
    / "processed"
    / "scored_observations.parquet"
)
OUTPUT_DIRECTORY = Path("data") / "processed"
CLUSTERED_PARQUET_PATH = (
    OUTPUT_DIRECTORY
    / "clustered_observations.parquet"
)
CLUSTERED_CSV_PATH = (
    OUTPUT_DIRECTORY
    / "clustered_observations.csv"
)
CLUSTER_SUMMARY_CSV_PATH = (
    OUTPUT_DIRECTORY
    / "alert_cluster_summary.csv"
)
CLUSTER_SUMMARY_JSON_PATH = (
    OUTPUT_DIRECTORY
    / "alert_cluster_summary.json"
)


def main() -> None:
    """Load alerts, cluster them, and save investigation summaries."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Scored observations are missing. Run "
            "'python scripts/train_detector.py' first."
        )

    scored_observations = pd.read_parquet(
        INPUT_PATH
    )

    clustered_observations = cluster_alerts(
        scored_observations=scored_observations,
        maximum_distance_metres=200.0,
        minimum_observations=5,
    )
    cluster_summary = summarise_alert_clusters(
        clustered_observations
    )

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    clustered_observations.to_parquet(
        CLUSTERED_PARQUET_PATH,
        index=False,
    )
    clustered_observations.to_csv(
        CLUSTERED_CSV_PATH,
        index=False,
    )
    cluster_summary.to_csv(
        CLUSTER_SUMMARY_CSV_PATH,
        index=False,
    )
    cluster_summary.to_json(
        CLUSTER_SUMMARY_JSON_PATH,
        orient="records",
        date_format="iso",
        indent=2,
    )

    alert_mask = clustered_observations[
        "predicted_anomaly"
    ].astype(bool)
    clustered_mask = (
        clustered_observations["cluster_id"] >= 0
    )
    spatial_noise_mask = (
        alert_mask & (~clustered_mask)
    )

    print("CellDefense spatial clustering complete")
    print(
        "Point alerts before clustering: "
        f"{int(alert_mask.sum()):,}"
    )
    print(
        "Alerts assigned to clusters: "
        f"{int((alert_mask & clustered_mask).sum()):,}"
    )
    print(
        "Isolated alerts treated as spatial noise: "
        f"{int(spatial_noise_mask.sum()):,}"
    )
    print(
        "Investigation clusters: "
        f"{len(cluster_summary):,}"
    )
    print("")

    if cluster_summary.empty:
        print("No corroborated investigation areas found.")
    else:
        print("Cluster summary:")
        print(
            cluster_summary.to_string(
                index=False
            )
        )

    print("")
    print(
        "Clustered observations: "
        f"{CLUSTERED_PARQUET_PATH}"
    )
    print(
        "Cluster summary: "
        f"{CLUSTER_SUMMARY_CSV_PATH}"
    )


if __name__ == "__main__":
    main()