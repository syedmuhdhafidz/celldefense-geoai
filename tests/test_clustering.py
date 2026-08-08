import pandas as pd
import pytest

from celldefense.anomalies import inject_cloned_cell
from celldefense.clustering import (
    cluster_alerts,
    summarise_alert_clusters,
)
from celldefense.features import build_feature_table
from celldefense.generator import (
    generate_baseline_observations,
)
from celldefense.model import (
    score_feature_table,
    train_anomaly_detector,
)


@pytest.fixture(scope="module")
def scored_scenario() -> pd.DataFrame:
    training_observations = (
        generate_baseline_observations(
            samples_per_route=200,
            random_seed=2026,
        )
    )
    scenario_baseline = (
        generate_baseline_observations(
            samples_per_route=200,
            random_seed=3030,
        )
    )
    scenario_observations = inject_cloned_cell(
        observations=scenario_baseline,
        start_fraction=0.40,
        end_fraction=0.60,
        random_seed=4040,
    )

    training_features = build_feature_table(
        training_observations
    )
    scenario_features = build_feature_table(
        scenario_observations
    )
    detector = train_anomaly_detector(
        baseline_features=training_features,
    )

    return score_feature_table(
        detector=detector,
        features=scenario_features,
    )


def test_spatial_clustering_finds_dense_alert_area(
    scored_scenario: pd.DataFrame,
) -> None:
    clustered = cluster_alerts(
        scored_scenario,
        maximum_distance_metres=200.0,
        minimum_observations=5,
    )
    summary = summarise_alert_clusters(clustered)

    assert not summary.empty
    assert summary.iloc[0]["observation_count"] >= 35
    assert (
        summary.iloc[0]["true_anomaly_fraction"]
        >= 0.90
    )


def test_non_alerts_remain_unclustered(
    scored_scenario: pd.DataFrame,
) -> None:
    clustered = cluster_alerts(scored_scenario)

    non_alerts = clustered.loc[
        ~clustered["predicted_anomaly"]
    ]

    assert set(non_alerts["cluster_id"]) == {-1}


def test_alerts_from_different_cells_are_not_merged() -> None:
    alerts = pd.DataFrame(
        {
            "timestamp": pd.date_range(
                start="2026-08-01 08:00:00+08:00",
                periods=6,
                freq="s"
            ),
            "latitude": [2.9205] * 6,
            "longitude": [101.6685] * 6,
            "cell_id": [
                "cell-001",
                "cell-001",
                "cell-001",
                "cell-001",
                "cell-001",
                "cell-004",
            ],
            "predicted_anomaly": [True] * 6,
        }
    )

    clustered = cluster_alerts(
        alerts,
        maximum_distance_metres=200.0,
        minimum_observations=5,
    )

    cell_001_clusters = set(
        clustered.loc[
            clustered["cell_id"] == "cell-001",
            "cluster_id",
        ]
    )
    cell_004_clusters = set(
        clustered.loc[
            clustered["cell_id"] == "cell-004",
            "cluster_id",
        ]
    )

    assert cell_001_clusters == {0}
    assert cell_004_clusters == {-1}


def test_separate_alert_periods_are_not_merged() -> None:
    first_period = pd.date_range(
        start="2026-08-01 08:00:00+08:00",
        periods=5,
        freq="s",
    )
    second_period = pd.date_range(
        start="2026-08-01 08:10:00+08:00",
        periods=5,
        freq="s",
    )

    alerts = pd.DataFrame(
        {
            "timestamp": [
                *first_period,
                *second_period,
            ],
            "latitude": [2.9205] * 10,
            "longitude": [101.6685] * 10,
            "cell_id": ["cell-001"] * 10,
            "predicted_anomaly": [True] * 10,
        }
    )

    clustered = cluster_alerts(
        alerts,
        maximum_distance_metres=200.0,
        maximum_time_gap_seconds=120.0,
        minimum_observations=5,
    )

    first_cluster_ids = set(
        clustered.iloc[:5]["cluster_id"]
    )
    second_cluster_ids = set(
        clustered.iloc[5:]["cluster_id"]
    )

    assert first_cluster_ids == {0}
    assert second_cluster_ids == {1}


def test_no_alerts_produce_empty_summary(
    scored_scenario: pd.DataFrame,
) -> None:
    no_alerts = scored_scenario.copy(deep=True)
    no_alerts["predicted_anomaly"] = False

    clustered = cluster_alerts(no_alerts)
    summary = summarise_alert_clusters(clustered)

    assert summary.empty
    assert set(clustered["cluster_id"]) == {-1}


def test_invalid_cluster_distance_is_rejected(
    scored_scenario: pd.DataFrame,
) -> None:
    with pytest.raises(
        ValueError,
        match="maximum_distance_metres must be positive",
    ):
        cluster_alerts(
            scored_scenario,
            maximum_distance_metres=0.0,
        )