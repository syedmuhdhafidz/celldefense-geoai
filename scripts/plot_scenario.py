"""Plot the synthetic cloned-cell anomaly scenario."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FormatStrFormatter

from celldefense.config import CYBERJAYA_AOI
from celldefense.network import (
    SYNTHETIC_BASE_STATIONS,
)
from celldefense.schema import validate_observations


DATA_PATH = (
    Path("data")
    / "synthetic"
    / "scenario_observations.parquet"
)
OUTPUT_PATH = (
    Path("docs")
    / "cloned_cell_scenario_map.png"
)

CLONED_CELL_ID = "cell-001"

RAT_STYLES = {
    "LTE": {
        "marker": "^",
        "colour": "#d62728",
    },
    "NR": {
        "marker": "s",
        "colour": "#9467bd",
    },
}


def main() -> None:
    """Load and plot the cloned-cell scenario."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Scenario data is missing. Run "
            "'python scripts/generate_scenario_dataset.py' "
            "first."
        )

    observations = pd.read_parquet(DATA_PATH)
    validate_observations(observations)

    anomalies = observations.loc[
        observations["is_anomaly"]
    ].copy()

    if anomalies.empty:
        raise ValueError(
            "The scenario dataset contains no anomalies."
        )

    cloned_station = next(
        station
        for station in SYNTHETIC_BASE_STATIONS
        if station.cell_id == CLONED_CELL_ID
    )

    anomaly_centre_latitude = float(
        anomalies["latitude"].mean()
    )
    anomaly_centre_longitude = float(
        anomalies["longitude"].mean()
    )

    figure, axis = plt.subplots(
        figsize=(11, 9),
    )

    for route_number, (
        route_id,
        route_data,
    ) in enumerate(
        observations.groupby(
            "route_id",
            sort=True,
        )
    ):
        axis.plot(
            route_data["longitude"],
            route_data["latitude"],
            color="#9aa0a6",
            linewidth=1.8,
            alpha=0.8,
            label=(
                "Simulated drive routes"
                if route_number == 0
                else None
            ),
        )

    for rat, style in RAT_STYLES.items():
        matching_stations = [
            station
            for station in SYNTHETIC_BASE_STATIONS
            if station.rat == rat
        ]

        axis.scatter(
            [
                station.longitude
                for station in matching_stations
            ],
            [
                station.latitude
                for station in matching_stations
            ],
            marker=style["marker"],
            color=style["colour"],
            edgecolor="black",
            linewidth=0.8,
            s=100,
            zorder=4,
            label=f"Synthetic {rat} station",
        )

    axis.scatter(
        anomalies["longitude"],
        anomalies["latitude"],
        color="#ff1744",
        edgecolor="white",
        linewidth=0.4,
        s=34,
        alpha=0.9,
        zorder=6,
        label="Cloned-cell observations",
    )

    axis.scatter(
        [anomaly_centre_longitude],
        [anomaly_centre_latitude],
        marker="X",
        color="black",
        edgecolor="white",
        linewidth=1.0,
        s=180,
        zorder=7,
        label="Anomaly cluster centre",
    )

    axis.plot(
        [
            cloned_station.longitude,
            anomaly_centre_longitude,
        ],
        [
            cloned_station.latitude,
            anomaly_centre_latitude,
        ],
        color="#ff1744",
        linestyle="--",
        linewidth=2.0,
        alpha=0.8,
        zorder=3,
        label="Geographic inconsistency",
    )

    axis.annotate(
        "Legitimate location\nof cloned cell-001",
        xy=(
            cloned_station.longitude,
            cloned_station.latitude,
        ),
        xytext=(12, 12),
        textcoords="offset points",
        fontsize=9,
        fontweight="bold",
        arrowprops={
            "arrowstyle": "->",
            "color": "#333333",
        },
    )

    axis.annotate(
        f"Suspicious cluster\n{len(anomalies)} observations",
        xy=(
            anomaly_centre_longitude,
            anomaly_centre_latitude,
        ),
        xytext=(14, -36),
        textcoords="offset points",
        fontsize=9,
        fontweight="bold",
        arrowprops={
            "arrowstyle": "->",
            "color": "#333333",
        },
    )

    axis.set_xlim(
        CYBERJAYA_AOI.minimum_longitude,
        CYBERJAYA_AOI.maximum_longitude,
    )
    axis.set_ylim(
        CYBERJAYA_AOI.minimum_latitude,
        CYBERJAYA_AOI.maximum_latitude,
    )

    axis.set_title(
        "CellDefense GeoAI: Cloned-Cell Scenario\n"
        "Synthetic geographic inconsistency",
        fontsize=15,
        fontweight="bold",
    )
    axis.set_xlabel("Longitude")
    axis.set_ylabel("Latitude")
    axis.xaxis.set_major_formatter(
        FormatStrFormatter("%.2f")
    )
    axis.yaxis.set_major_formatter(
        FormatStrFormatter("%.2f")
    )
    axis.grid(
        visible=True,
        linestyle="--",
        linewidth=0.6,
        alpha=0.5,
    )
    axis.set_aspect(
        "equal",
        adjustable="box",
    )
    axis.legend(
        loc="upper left",
        fontsize=8,
    )

    figure.text(
        0.5,
        0.015,
        (
            "Synthetic decision-support demonstration only. "
            "This is not evidence of a real rogue base station."
        ),
        ha="center",
        fontsize=9,
        color="#555555",
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    figure.tight_layout(
        rect=(0.0, 0.04, 1.0, 1.0),
    )
    figure.savefig(
        OUTPUT_PATH,
        dpi=180,
        bbox_inches="tight",
    )
    plt.close(figure)

    print(f"Loaded observations: {len(observations):,}")
    print(f"Anomaly observations: {len(anomalies):,}")
    print(
        "Anomaly centre: "
        f"{anomaly_centre_latitude:.5f}, "
        f"{anomaly_centre_longitude:.5f}"
    )
    print(f"Map saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()