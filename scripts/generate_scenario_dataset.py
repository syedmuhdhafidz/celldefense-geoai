"""Generate the labelled CellDefense scenario dataset."""

from pathlib import Path

from celldefense.anomalies import inject_cloned_cell
from celldefense.generator import (
    generate_baseline_observations,
)
from celldefense.schema import validate_observations


OUTPUT_DIRECTORY = Path("data") / "synthetic"
PARQUET_OUTPUT_PATH = (
    OUTPUT_DIRECTORY / "scenario_observations.parquet"
)
CSV_OUTPUT_PATH = (
    OUTPUT_DIRECTORY / "scenario_observations.csv"
)


def main() -> None:
    """Generate, inject, validate, and save scenario observations."""

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    baseline = generate_baseline_observations(
        samples_per_route=600,
    )

    observations = inject_cloned_cell(
        observations=baseline,
        route_id="route-west-east",
        cloned_cell_id="cell-001",
        start_fraction=0.55,
        end_fraction=0.70,
        random_seed=2027,
    )

    validate_observations(observations)

    observations.to_parquet(
        PARQUET_OUTPUT_PATH,
        index=False,
    )
    observations.to_csv(
        CSV_OUTPUT_PATH,
        index=False,
    )

    scenario_counts = (
        observations["scenario"]
        .value_counts()
        .sort_index()
    )
    anomaly_count = int(
        observations["is_anomaly"].sum()
    )
    anomaly_percentage = (
        anomaly_count / len(observations)
    ) * 100.0

    print("CellDefense scenario generation complete")
    print(f"Observations: {len(observations):,}")
    print(f"Anomalies: {anomaly_count:,}")
    print(
        f"Anomaly rate: {anomaly_percentage:.2f}%"
    )
    print("Scenario counts:")

    for scenario, count in scenario_counts.items():
        print(f"  {scenario}: {count:,}")

    print(f"Parquet: {PARQUET_OUTPUT_PATH}")
    print(f"CSV: {CSV_OUTPUT_PATH}")


if __name__ == "__main__":
    main()