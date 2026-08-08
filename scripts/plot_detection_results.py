"""Plot model alerts and corroborated investigation clusters."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FormatStrFormatter

from celldefense.config import CYBERJAYA_AOI
from celldefense.network import (
    SYNTHETIC_BASE_STATIONS,
)

INPUT_PATH = (
    Path("data")
    / "processed"
    / "clustered_observations.parquet"
)
OUTPUT_PATH = (
    Path("docs")
    / "detection_results_map.png"
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
    """Plot point alerts and prioritised investigation areas."""

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            "Clustered observations are missing. Run "
            "'python scripts/cluster_alerts.py' first."
        )

    observations = pd.read_parquet(INPUT_PATH)

    required_columns = {
        "latitude",
        "longitude",
        "route_id",
        "cell_id",
        "predicted_anomaly",
        "threat_score",
        "cluster_id",
    }
    missing_columns = required_columns - set(
        observations.columns
    )
    if missing_columns:
        raise ValueError(
            f"Missing plotting columns: "
            f"{sorted(missing_columns)}"
        )

    alert_mask = observations[
        "predicted_anomaly"
    ].astype(bool)
    clustered_mask = (
        observations["cluster_id"] >= 0
    )
    routine_mask = ~alert_mask
    spatial_noise_mask = (
        alert_mask & (~clustered_mask)
    )
    corroborated_mask = (
        alert_mask & clustered_mask
    )

    routine_observations = observations.loc[
        routine_mask
    ]
    spatial_noise = observations.loc[
        spatial_noise_mask
    ]
    corroborated_alerts = observations.loc[
        corroborated_mask
    ]

    station_by_cell_id = {
        station.cell_id: station
        for station in SYNTHETIC_BASE_STATIONS
    }

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
            color="#aeb4ba",
            linewidth=1.6,
            alpha=0.75,
            zorder=1,
            label=(
                "Simulated drive routes"
                if route_number == 0
                else None
            ),
        )

    axis.scatter(
        routine_observations["longitude"],
        routine_observations["latitude"],
        color="#78909c",
        s=8,
        alpha=0.22,
        linewidth=0,
        zorder=2,
        label="Routine observations",
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
            zorder=5,
            label=f"Synthetic {rat} station",
        )

    if not spatial_noise.empty:
        axis.scatter(
            spatial_noise["longitude"],
            spatial_noise["latitude"],
            marker="D",
            color="#ff9800",
            edgecolor="white",
            linewidth=0.5,
            s=42,
            alpha=0.9,
            zorder=6,
            label=(
                "Isolated point alerts "
                "(not escalated)"
            ),
        )

    if not corroborated_alerts.empty:
        axis.scatter(
            corroborated_alerts["longitude"],
            corroborated_alerts["latitude"],
            color="#ff1744",
            edgecolor="white",
            linewidth=0.45,
            s=38,
            alpha=0.9,
            zorder=7,
            label=(
                "Corroborated priority alerts"
            ),
        )

    for cluster_id, cluster_data in (
        corroborated_alerts.groupby(
            "cluster_id",
            sort=True,
        )
    ):
        centroid_latitude = float(
            cluster_data["latitude"].mean()
        )
        centroid_longitude = float(
            cluster_data["longitude"].mean()
        )
        maximum_threat_score = float(
            cluster_data["threat_score"].max()
        )
        dominant_cell_id = (
            cluster_data["cell_id"]
            .mode()
            .iloc[0]
        )

        axis.scatter(
            [centroid_longitude],
            [centroid_latitude],
            marker="X",
            color="black",
            edgecolor="white",
            linewidth=1.0,
            s=190,
            zorder=8,
            label=(
                "Investigation cluster centre"
                if int(cluster_id) == 0
                else None
            ),
        )

        axis.annotate(
            (
                f"Priority area {int(cluster_id) + 1}\n"
                f"{len(cluster_data)} corroborated alerts\n"
                f"Maximum threat score: "
                f"{maximum_threat_score:.0f}/100\n"
                f"Reported identity: "
                f"{dominant_cell_id}"
            ),
            xy=(
                centroid_longitude,
                centroid_latitude,
            ),
            xytext=(16, -70),
            textcoords="offset points",
            fontsize=9,
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.45",
                "facecolor": "white",
                "edgecolor": "#ff1744",
                "alpha": 0.95,
            },
            arrowprops={
                "arrowstyle": "->",
                "color": "#333333",
            },
            zorder=9,
        )

        reported_station = station_by_cell_id.get(
            dominant_cell_id
        )

        if reported_station is not None:
            axis.plot(
                [
                    reported_station.longitude,
                    centroid_longitude,
                ],
                [
                    reported_station.latitude,
                    centroid_latitude,
                ],
                color="#ff1744",
                linestyle="--",
                linewidth=2.0,
                alpha=0.8,
                zorder=4,
                label=(
                    "Reported-location inconsistency"
                    if int(cluster_id) == 0
                    else None
                ),
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
        "CellDefense GeoAI: Detection and Spatial Corroboration\n"
        "Suspicious base-station anomaly triage",
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
            "Alerts indicate areas for further investigation, "
            "not confirmed rogue base stations."
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

    print("CellDefense detection map complete")
    print(
        "Routine observations: "
        f"{len(routine_observations):,}"
    )
    print(
        "Isolated point alerts: "
        f"{len(spatial_noise):,}"
    )
    print(
        "Corroborated alerts: "
        f"{len(corroborated_alerts):,}"
    )
    print(
        "Investigation clusters: "
        f"{corroborated_alerts['cluster_id'].nunique():,}"
    )
    print(f"Map saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()