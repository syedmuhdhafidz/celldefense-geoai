"""Generate and save the CellDefense baseline RF dataset."""

from pathlib import Path

from celldefense.generator import (
    generate_baseline_observations,
)
from celldefense.schema import validate_observations


OUTPUT_DIRECTORY = Path("data") / "synthetic"
PARQUET_OUTPUT_PATH = (
    OUTPUT_DIRECTORY / "baseline_observations.parquet"
)
CSV_OUTPUT_PATH = (
    OUTPUT_DIRECTORY / "baseline_observations.csv"
)


def main() -> None:
    """Generate, validate, summarise, and save the baseline dataset."""

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    observations = generate_baseline_observations(
        samples_per_route=600,
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

    print("CellDefense baseline generation complete")
    print(f"Observations: {len(observations):,}")
    print(
        f"Routes: {observations['route_id'].nunique()}"
    )
    print(
        "Time range: "
        f"{observations['timestamp'].min()} to "
        f"{observations['timestamp'].max()}"
    )
    print(
        "RSRP range: "
        f"{observations['rsrp_dbm'].min():.2f} to "
        f"{observations['rsrp_dbm'].max():.2f} dBm"
    )
    print(
        "Handover events: "
        f"{int(observations['handover_event'].sum())}"
    )
    print(f"Parquet: {PARQUET_OUTPUT_PATH}")
    print(f"CSV: {CSV_OUTPUT_PATH}")


if __name__ == "__main__":
    main()