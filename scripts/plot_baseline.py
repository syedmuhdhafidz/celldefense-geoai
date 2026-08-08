"""Plot the baseline routes and synthetic base-station topology."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FormatStrFormatter

from celldefense.config import CYBERJAYA_AOI
from celldefense.network import (
    SYNTHETIC_BASE_STATIONS,
    validate_network,
)
from celldefense.schema import validate_observations


DATA_PATH = (
    Path("data")
    / "synthetic"
    / "baseline_observations.parquet"
)
OUTPUT_PATH = (
    Path("docs")
    / "baseline_network_map.png"
)

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
    """Load, validate, and plot the baseline network."""

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Baseline data is missing. Run "
            "'python scripts/generate_baseline.py' first."
        )

    observations = pd.read_parquet(DATA_PATH)
    validate_observations(observations)
    validate_network(SYNTHETIC_BASE_STATIONS)

    figure, axis = plt.subplots(
        figsize=(11, 9),
    )

    for route_id, route_data in observations.groupby(
        "route_id",
        sort=True,
    ):
        axis.plot(
            route_data["longitude"],
            route_data["latitude"],
            linewidth=2.2,
            alpha=0.85,
            label=route_id,
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
            s=130,
            zorder=5,
            label=f"Synthetic {rat} station",
        )

    for station in SYNTHETIC_BASE_STATIONS:
        axis.annotate(
            station.cell_id,
            xy=(
                station.longitude,
                station.latitude,
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
            fontweight="bold",
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
        "CellDefense GeoAI Baseline Network\n"
        "Synthetic routes and fictional base stations",
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
            "For simulation only — markers do not represent "
            "real telecommunications infrastructure."
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
    print(
        "Synthetic stations: "
        f"{len(SYNTHETIC_BASE_STATIONS)}"
    )
    print(f"Map saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()