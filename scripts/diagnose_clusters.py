"""Diagnose feature differences between spatial alert clusters."""

from pathlib import Path

import pandas as pd

from celldefense.features import MODEL_FEATURE_COLUMNS


INPUT_PATH = (
    Path("data")
    / "processed"
    / "clustered_observations.parquet"
)
DIAGNOSTIC_OUTPUT_PATH = (
    Path("data")
    / "processed"
    / "cluster_feature_diagnostics.csv"
)


def main() -> None:
    """Compare cluster features with normal observation ranges."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Clustered observations are missing. Run "
            "'python scripts/cluster_alerts.py' first."
        )

    observations = pd.read_parquet(INPUT_PATH)

    normal_observations = observations.loc[
        ~observations["is_anomaly"]
    ]

    if normal_observations.empty:
        raise ValueError(
            "No normal observations are available "
            "for comparison."
        )

    cluster_ids = sorted(
        int(cluster_id)
        for cluster_id in observations.loc[
            observations["cluster_id"] >= 0,
            "cluster_id",
        ].unique()
    )

    diagnostic_rows: list[dict[str, object]] = []

    for cluster_id in cluster_ids:
        cluster_data = observations.loc[
            observations["cluster_id"]
            == cluster_id
        ]

        for feature in MODEL_FEATURE_COLUMNS:
            normal_p01 = float(
                normal_observations[
                    feature
                ].quantile(0.01)
            )
            normal_median = float(
                normal_observations[
                    feature
                ].median()
            )
            normal_p99 = float(
                normal_observations[
                    feature
                ].quantile(0.99)
            )
            cluster_minimum = float(
                cluster_data[feature].min()
            )
            cluster_median = float(
                cluster_data[feature].median()
            )
            cluster_maximum = float(
                cluster_data[feature].max()
            )

            median_outside_normal_range = bool(
                cluster_median < normal_p01
                or cluster_median > normal_p99
            )

            diagnostic_rows.append(
                {
                    "cluster_id": cluster_id,
                    "feature": feature,
                    "normal_p01": round(
                        normal_p01,
                        3,
                    ),
                    "normal_median": round(
                        normal_median,
                        3,
                    ),
                    "normal_p99": round(
                        normal_p99,
                        3,
                    ),
                    "cluster_minimum": round(
                        cluster_minimum,
                        3,
                    ),
                    "cluster_median": round(
                        cluster_median,
                        3,
                    ),
                    "cluster_maximum": round(
                        cluster_maximum,
                        3,
                    ),
                    (
                        "cluster_median_outside_"
                        "normal_98_percent_range"
                    ): median_outside_normal_range,
                }
            )

    diagnostics = pd.DataFrame(
        diagnostic_rows
    )
    diagnostics.to_csv(
        DIAGNOSTIC_OUTPUT_PATH,
        index=False,
    )

    print("CellDefense cluster diagnosis")
    print(
        f"Normal observations used: "
        f"{len(normal_observations):,}"
    )
    print(f"Clusters examined: {cluster_ids}")
    print("")

    for cluster_id in cluster_ids:
        cluster_data = observations.loc[
            observations["cluster_id"]
            == cluster_id
        ]
        cluster_diagnostics = diagnostics.loc[
            diagnostics["cluster_id"]
            == cluster_id
        ]
        unusual_features = (
            cluster_diagnostics.loc[
                cluster_diagnostics[
                    (
                        "cluster_median_outside_"
                        "normal_98_percent_range"
                    )
                ]
            ]
        )

        print(f"Cluster {cluster_id}")
        print(
            f"  Observations: "
            f"{len(cluster_data):,}"
        )
        print(
            f"  True anomaly fraction: "
            f"{cluster_data['is_anomaly'].mean():.4f}"
        )
        print(
            f"  Route: "
            f"{cluster_data['route_id'].mode().iloc[0]}"
        )
        print(
            f"  Cell: "
            f"{cluster_data['cell_id'].mode().iloc[0]}"
        )
        print(
            "  Time range: "
            f"{cluster_data['timestamp'].min()} to "
            f"{cluster_data['timestamp'].max()}"
        )
        print("  Unusual median features:")

        if unusual_features.empty:
            print("    None")
        else:
            for row in unusual_features.itertuples(
                index=False
            ):
                print(
                    f"    {row.feature}: "
                    f"cluster median="
                    f"{row.cluster_median}, "
                    f"normal p01="
                    f"{row.normal_p01}, "
                    f"normal p99="
                    f"{row.normal_p99}"
                )

        print("")

    false_positive_rows = observations.loc[
        (observations["cluster_id"] >= 0)
        & (~observations["is_anomaly"])
    ]

    print("False-positive alert rows:")
    print(
        false_positive_rows[
            [
                "timestamp",
                "route_id",
                "cell_id",
                "latitude",
                "longitude",
                "rsrp_dbm",
                "expected_rsrp_dbm",
                "rsrp_residual_db",
                "absolute_rsrp_residual_db",
                "distance_to_reported_cell_m",
                "handover_event_int",
                "threat_score",
                "cluster_id",
            ]
        ].to_string(index=False)
    )
    print("")
    print(
        f"Full diagnostics saved to: "
        f"{DIAGNOSTIC_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()