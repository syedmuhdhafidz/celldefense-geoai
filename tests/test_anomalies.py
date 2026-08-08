import pandas as pd
import pytest

from celldefense.anomalies import inject_cloned_cell
from celldefense.generator import (
    generate_baseline_observations,
)
from celldefense.schema import validate_observations


def test_cloned_cell_injection_preserves_row_count() -> None:
    baseline = generate_baseline_observations(
        samples_per_route=100,
    )
    original_baseline = baseline.copy(deep=True)

    result = inject_cloned_cell(
        observations=baseline,
        start_fraction=0.40,
        end_fraction=0.60,
    )

    assert len(result) == len(baseline)
    pd.testing.assert_frame_equal(
        baseline,
        original_baseline,
    )


def test_cloned_cell_injection_creates_expected_labels() -> None:
    baseline = generate_baseline_observations(
        samples_per_route=100,
    )

    result = inject_cloned_cell(
        observations=baseline,
        route_id="route-west-east",
        cloned_cell_id="cell-001",
        start_fraction=0.40,
        end_fraction=0.60,
    )

    anomalies = result.loc[result["is_anomaly"]]

    assert len(anomalies) == 20
    assert set(anomalies["scenario"]) == {
        "cloned_cell"
    }
    assert set(anomalies["route_id"]) == {
        "route-west-east"
    }
    assert set(anomalies["cell_id"]) == {
        "cell-001"
    }
    assert set(anomalies["neighbour_count"]) == {1}

    validate_observations(result)


def test_cloned_cell_injection_is_deterministic() -> None:
    baseline = generate_baseline_observations(
        samples_per_route=100,
    )

    first_result = inject_cloned_cell(
        observations=baseline,
        random_seed=2027,
    )
    second_result = inject_cloned_cell(
        observations=baseline,
        random_seed=2027,
    )

    pd.testing.assert_frame_equal(
        first_result,
        second_result,
    )


def test_unknown_route_is_rejected() -> None:
    baseline = generate_baseline_observations(
        samples_per_route=20,
    )

    with pytest.raises(
        ValueError,
        match="Unknown or empty route_id",
    ):
        inject_cloned_cell(
            observations=baseline,
            route_id="route-does-not-exist",
        )