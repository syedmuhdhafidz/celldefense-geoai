import pandas as pd
import pytest

from celldefense.anomalies import inject_cloned_cell
from celldefense.features import build_feature_table
from celldefense.generator import (
    generate_baseline_observations,
)
from celldefense.model import (
    evaluate_predictions,
    score_feature_table,
    train_anomaly_detector,
)


def build_training_and_scenario_features() -> (
    tuple[pd.DataFrame, pd.DataFrame]
):
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

    return (
        build_feature_table(training_observations),
        build_feature_table(scenario_observations),
    )


def test_training_rejects_anomalous_data() -> None:
    _, scenario_features = (
        build_training_and_scenario_features()
    )

    with pytest.raises(
        ValueError,
        match="baseline observations only",
    ):
        train_anomaly_detector(
            baseline_features=scenario_features,
        )


def test_scoring_adds_expected_output_columns() -> None:
    training_features, scenario_features = (
        build_training_and_scenario_features()
    )
    detector = train_anomaly_detector(
        baseline_features=training_features,
    )

    scored = score_feature_table(
        detector=detector,
        features=scenario_features,
    )

    assert {
        "raw_anomaly_score",
        "threat_score",
        "predicted_anomaly",
    }.issubset(scored.columns)
    assert scored["threat_score"].between(
        0.0,
        100.0,
    ).all()


def test_detector_finds_cloned_cell_scenario() -> None:
    training_features, scenario_features = (
        build_training_and_scenario_features()
    )
    detector = train_anomaly_detector(
        baseline_features=training_features,
        target_false_positive_rate=0.01,
    )
    scored = score_feature_table(
        detector=detector,
        features=scenario_features,
    )
    metrics = evaluate_predictions(scored)

    assert metrics["recall"] >= 0.90
    assert metrics["false_positive_rate"] <= 0.05


def test_detector_results_are_deterministic() -> None:
    training_features, scenario_features = (
        build_training_and_scenario_features()
    )

    first_detector = train_anomaly_detector(
        baseline_features=training_features,
        random_seed=2026,
    )
    second_detector = train_anomaly_detector(
        baseline_features=training_features,
        random_seed=2026,
    )

    first_scores = score_feature_table(
        detector=first_detector,
        features=scenario_features,
    )
    second_scores = score_feature_table(
        detector=second_detector,
        features=scenario_features,
    )

    pd.testing.assert_series_equal(
        first_scores["threat_score"],
        second_scores["threat_score"],
    )