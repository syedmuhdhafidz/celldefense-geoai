import numpy as np
import pandas as pd

from celldefense.anomalies import inject_cloned_cell
from celldefense.features import (
    MODEL_FEATURE_COLUMNS,
    UNKNOWN_CELL_DISTANCE_METRES,
    UNKNOWN_CELL_EXPECTED_RSRP_DBM,
    build_feature_table,
)
from celldefense.generator import (
    generate_baseline_observations,
)


def test_feature_table_preserves_row_count() -> None:
    observations = generate_baseline_observations(
        samples_per_route=20,
    )

    features = build_feature_table(observations)

    assert len(features) == len(observations)
    assert set(MODEL_FEATURE_COLUMNS).issubset(
        features.columns
    )


def test_all_model_features_are_finite() -> None:
    observations = generate_baseline_observations(
        samples_per_route=20,
    )

    features = build_feature_table(observations)

    assert np.isfinite(
        features[MODEL_FEATURE_COLUMNS].to_numpy(
            dtype=float
        )
    ).all()


def test_cloned_cell_has_larger_signal_residual() -> None:
    baseline = generate_baseline_observations(
        samples_per_route=100,
    )
    scenario = inject_cloned_cell(
        observations=baseline,
        start_fraction=0.40,
        end_fraction=0.60,
    )

    features = build_feature_table(scenario)

    baseline_residual = features.loc[
        ~features["is_anomaly"],
        "absolute_rsrp_residual_db",
    ].median()
    anomaly_residual = features.loc[
        features["is_anomaly"],
        "absolute_rsrp_residual_db",
    ].median()

    baseline_inconsistency = features.loc[
        ~features["is_anomaly"],
        "signal_distance_inconsistency",
    ].median()
    anomaly_inconsistency = features.loc[
        features["is_anomaly"],
        "signal_distance_inconsistency",
    ].median()

    assert anomaly_residual > baseline_residual
    assert anomaly_inconsistency > baseline_inconsistency


def test_unknown_cell_uses_safe_fallback_features() -> None:
    observations = generate_baseline_observations(
        samples_per_route=20,
    )
    modified_observations = observations.copy(
        deep=True
    )
    modified_observations.loc[
        0,
        "cell_id",
    ] = "unknown-cell"

    features = build_feature_table(
        modified_observations
    )
    unknown_features = features.iloc[0]

    assert unknown_features["known_cell"] == 0
    assert (
        unknown_features[
            "distance_to_reported_cell_m"
        ]
        == UNKNOWN_CELL_DISTANCE_METRES
    )
    assert (
        unknown_features["expected_rsrp_dbm"]
        == UNKNOWN_CELL_EXPECTED_RSRP_DBM
    )

    pd.testing.assert_frame_equal(
        observations,
        observations.copy(deep=True),
    )