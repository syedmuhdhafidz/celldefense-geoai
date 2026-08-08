import pandas as pd

from celldefense.generator import (
    generate_baseline_observations,
)
from celldefense.routes import SYNTHETIC_ROUTES
from celldefense.schema import (
    REQUIRED_COLUMNS,
    validate_observations,
)


def test_generator_returns_expected_number_of_rows() -> None:
    observations = generate_baseline_observations(
        samples_per_route=50,
    )

    assert len(observations) == (
        len(SYNTHETIC_ROUTES) * 50
    )


def test_generated_observations_follow_data_contract() -> None:
    observations = generate_baseline_observations(
        samples_per_route=20,
    )

    validate_observations(observations)

    assert list(observations.columns) == REQUIRED_COLUMNS
    assert observations["observation_id"].is_unique


def test_baseline_generation_is_deterministic() -> None:
    first_result = generate_baseline_observations(
        samples_per_route=20,
        random_seed=2026,
    )
    second_result = generate_baseline_observations(
        samples_per_route=20,
        random_seed=2026,
    )

    pd.testing.assert_frame_equal(
        first_result,
        second_result,
    )


def test_baseline_contains_no_anomaly_labels() -> None:
    observations = generate_baseline_observations(
        samples_per_route=20,
    )

    assert set(observations["scenario"]) == {
        "baseline"
    }
    assert not observations["is_anomaly"].any()