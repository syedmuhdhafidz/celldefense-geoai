"""Interactive CellDefense GeoAI investigation dashboard."""

import json
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from celldefense.config import CYBERJAYA_AOI
from celldefense.network import (
    SYNTHETIC_BASE_STATIONS,
)

CLUSTERED_DATA_PATH = (
    Path("data")
    / "processed"
    / "clustered_observations.parquet"
)
CLUSTER_SUMMARY_PATH = (
    Path("data")
    / "processed"
    / "alert_cluster_summary.csv"
)
DIAGNOSTICS_PATH = (
    Path("data")
    / "processed"
    / "cluster_feature_diagnostics.csv"
)
EVALUATION_METRICS_PATH = (
    Path("data")
    / "processed"
    / "evaluation_metrics.json"
)

MAP_CENTRE = [
    (
        CYBERJAYA_AOI.minimum_latitude
        + CYBERJAYA_AOI.maximum_latitude
    )
    / 2,
    (
        CYBERJAYA_AOI.minimum_longitude
        + CYBERJAYA_AOI.maximum_longitude
    )
    / 2,
]


@st.cache_data
def load_dashboard_data() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, float | int],
]:
    """Load clustered observations and investigation summaries."""

    if not CLUSTERED_DATA_PATH.exists():
        raise FileNotFoundError(
            "Clustered observations are missing. Run "
            "'python scripts/cluster_alerts.py' first."
        )

    if not CLUSTER_SUMMARY_PATH.exists():
        raise FileNotFoundError(
            "The cluster summary is missing. Run "
            "'python scripts/cluster_alerts.py' first."
        )
        
    if not DIAGNOSTICS_PATH.exists():
        raise FileNotFoundError(
            "Cluster diagnostics are missing. Run "
            "'python scripts/diagnose_clusters.py' first."
        )

    if not EVALUATION_METRICS_PATH.exists():
        raise FileNotFoundError(
            "Evaluation metrics are missing. Run "
            "'python scripts/train_detector.py' first."
        )

    observations = pd.read_parquet(
        CLUSTERED_DATA_PATH
    )
    cluster_summary = pd.read_csv(
        CLUSTER_SUMMARY_PATH
    )
    for time_column in (
        "start_time",
        "end_time",
    ):
        cluster_summary[time_column] = (
            pd.to_datetime(
                cluster_summary[time_column],
                utc=True,
            ).dt.tz_convert(
                "Asia/Kuala_Lumpur"
            )
        )
        
    diagnostics = pd.read_csv(
        DIAGNOSTICS_PATH
    )
    evaluation_metrics = json.loads(
        EVALUATION_METRICS_PATH.read_text(
            encoding="utf-8"
        )
    )

    required_observation_columns = {
        "timestamp",
        "latitude",
        "longitude",
        "route_id",
        "cell_id",
        "predicted_anomaly",
        "threat_score",
        "cluster_id",
    }
    missing_observation_columns = (
        required_observation_columns
        - set(observations.columns)
    )
    if missing_observation_columns:
        raise ValueError(
            "Missing dashboard observation columns: "
            f"{sorted(missing_observation_columns)}"
        )

    observations["timestamp"] = pd.to_datetime(
        observations["timestamp"]
    )

    return (
        observations,
        cluster_summary,
        diagnostics,
        evaluation_metrics,
    )


def add_routes(
    map_object: folium.Map,
    observations: pd.DataFrame,
) -> None:
    """Add simulated collection routes to the map."""

    route_layer = folium.FeatureGroup(
        name="Simulated drive routes",
        show=True,
    )

    for route_id, route_data in observations.groupby(
        "route_id",
        sort=True,
    ):
        coordinates = list(
            zip(
                route_data["latitude"],
                route_data["longitude"],
            )
        )

        folium.PolyLine(
            locations=coordinates,
            color="#78909c",
            weight=3,
            opacity=0.65,
            tooltip=f"Route: {route_id}",
        ).add_to(route_layer)

    route_layer.add_to(map_object)


def add_synthetic_stations(
    map_object: folium.Map,
) -> None:
    """Add fictional base-station reference locations."""

    station_layer = folium.FeatureGroup(
        name="Synthetic reference stations",
        show=True,
    )

    for station in SYNTHETIC_BASE_STATIONS:
        station_colour = (
            "#d62728"
            if station.rat == "LTE"
            else "#7e57c2"
        )

        folium.CircleMarker(
            location=[
                station.latitude,
                station.longitude,
            ],
            radius=7,
            color="#212121",
            weight=2,
            fill=True,
            fill_color=station_colour,
            fill_opacity=0.95,
            tooltip=(
                f"{station.cell_id} "
                f"({station.rat})"
            ),
            popup=folium.Popup(
                (
                    "<strong>Synthetic reference station</strong>"
                    f"<br>Cell ID: {station.cell_id}"
                    f"<br>Radio technology: {station.rat}"
                    "<br>Status: fictional demonstration data"
                ),
                max_width=280,
            ),
        ).add_to(station_layer)

    station_layer.add_to(map_object)


def add_isolated_alerts(
    map_object: folium.Map,
    observations: pd.DataFrame,
) -> None:
    """Add point alerts that were not spatially corroborated."""

    alert_mask = observations[
        "predicted_anomaly"
    ].astype(bool)
    isolated_alerts = observations.loc[
        alert_mask
        & (observations["cluster_id"] < 0)
    ]

    noise_layer = folium.FeatureGroup(
        name="Isolated alerts — not escalated",
        show=True,
    )

    for alert in isolated_alerts.itertuples():
        folium.CircleMarker(
            location=[
                alert.latitude,
                alert.longitude,
            ],
            radius=5,
            color="#e65100",
            weight=1,
            fill=True,
            fill_color="#ff9800",
            fill_opacity=0.9,
            tooltip=(
                "Isolated alert — "
                f"score {alert.threat_score:.0f}/100"
            ),
            popup=folium.Popup(
                (
                    "<strong>Isolated point alert</strong>"
                    f"<br>Cell ID: {alert.cell_id}"
                    f"<br>Threat score: "
                    f"{alert.threat_score:.1f}/100"
                    "<br>Decision: not spatially corroborated"
                ),
                max_width=280,
            ),
        ).add_to(noise_layer)

    noise_layer.add_to(map_object)


def add_investigation_clusters(
    map_object: folium.Map,
    observations: pd.DataFrame,
    cluster_summary: pd.DataFrame,
) -> None:
    """Add corroborated alerts and prioritised investigation zones."""

    cluster_layer = folium.FeatureGroup(
        name="Corroborated priority alerts",
        show=True,
    )
    investigation_layer = folium.FeatureGroup(
        name="Investigation zones",
        show=True,
    )

    station_by_cell_id = {
        station.cell_id: station
        for station in SYNTHETIC_BASE_STATIONS
    }

    corroborated_alerts = observations.loc[
        observations["cluster_id"] >= 0
    ]

    for alert in corroborated_alerts.itertuples():
        folium.CircleMarker(
            location=[
                alert.latitude,
                alert.longitude,
            ],
            radius=4,
            color="#ffffff",
            weight=1,
            fill=True,
            fill_color="#ff1744",
            fill_opacity=0.9,
            tooltip=(
                "Corroborated alert — "
                f"score {alert.threat_score:.0f}/100"
            ),
            popup=folium.Popup(
                (
                    "<strong>Corroborated alert</strong>"
                    f"<br>Cluster: "
                    f"{int(alert.cluster_id) + 1}"
                    f"<br>Cell ID: {alert.cell_id}"
                    f"<br>Threat score: "
                    f"{alert.threat_score:.1f}/100"
                ),
                max_width=280,
            ),
        ).add_to(cluster_layer)

    for cluster in cluster_summary.itertuples():
        priority_number = int(
            cluster.cluster_id
        ) + 1

        folium.Circle(
            location=[
                cluster.centroid_latitude,
                cluster.centroid_longitude,
            ],
            radius=200,
            color="#d50000",
            weight=3,
            fill=True,
            fill_color="#ff1744",
            fill_opacity=0.12,
            tooltip=f"Priority area {priority_number}",
            popup=folium.Popup(
                (
                    f"<strong>Priority area "
                    f"{priority_number}</strong>"
                    f"<br>Reported cell: "
                    f"{cluster.dominant_cell_id}"
                    f"<br>Corroborated alerts: "
                    f"{cluster.observation_count}"
                    f"<br>Mean threat score: "
                    f"{cluster.mean_threat_score:.1f}/100"
                    f"<br>Maximum threat score: "
                    f"{cluster.maximum_threat_score:.1f}/100"
                    "<br>Recommended action: "
                    "further RF investigation"
                ),
                max_width=320,
            ),
        ).add_to(investigation_layer)

        folium.Marker(
            location=[
                cluster.centroid_latitude,
                cluster.centroid_longitude,
            ],
            tooltip=(
                f"Priority area {priority_number}"
            ),
            popup=(
                f"Investigation cluster "
                f"{priority_number}"
            ),
            icon=folium.Icon(
                color="red",
                icon="exclamation-triangle",
                prefix="fa",
            ),
        ).add_to(investigation_layer)

        reported_station = station_by_cell_id.get(
            cluster.dominant_cell_id
        )

        if reported_station is not None:
            folium.PolyLine(
                locations=[
                    [
                        reported_station.latitude,
                        reported_station.longitude,
                    ],
                    [
                        cluster.centroid_latitude,
                        cluster.centroid_longitude,
                    ],
                ],
                color="#ff1744",
                weight=3,
                opacity=0.85,
                dash_array="8 8",
                tooltip=(
                    "Reported-location inconsistency"
                ),
            ).add_to(investigation_layer)

    cluster_layer.add_to(map_object)
    investigation_layer.add_to(map_object)


def build_map(
    observations: pd.DataFrame,
    cluster_summary: pd.DataFrame,
) -> folium.Map:
    """Build the interactive investigation map."""

    map_object = folium.Map(
        location=MAP_CENTRE,
        zoom_start=13,
        tiles="CartoDB positron",
        control_scale=True,
    )

    add_routes(
        map_object,
        observations,
    )
    add_synthetic_stations(map_object)
    add_isolated_alerts(
        map_object,
        observations,
    )
    add_investigation_clusters(
        map_object,
        observations,
        cluster_summary,
    )

    folium.LayerControl(
        collapsed=False
    ).add_to(map_object)

    return map_object


def main() -> None:
    """Render the CellDefense dashboard."""

    st.set_page_config(
        page_title="CellDefense GeoAI",
        page_icon="🖥️",
        layout="wide",
    )

    st.title(
        "CellDefense GeoAI"
    )
    st.subheader(
        "Suspicious base-station anomaly triage"
    )

    st.info(
        "Synthetic decision-support demonstration for "
        "Cyberjaya. A priority area indicates where further "
        "RF investigation may be warranted; it does not "
        "confirm the presence of a rogue base station."
    )

    try:
        (
            observations,
            cluster_summary,
            diagnostics,
            evaluation_metrics,
        ) = load_dashboard_data()
    except (
        FileNotFoundError,
        ValueError,
    ) as error:
        st.error(str(error))
        st.stop()

    alert_mask = observations[
        "predicted_anomaly"
    ].astype(bool)
    clustered_mask = (
        observations["cluster_id"] >= 0
    )

    point_alert_count = int(
        alert_mask.sum()
    )
    corroborated_alert_count = int(
        (alert_mask & clustered_mask).sum()
    )
    isolated_alert_count = int(
        (alert_mask & (~clustered_mask)).sum()
    )
    investigation_cluster_count = len(
        cluster_summary
    )

    metric_columns = st.columns(4)

    metric_columns[0].metric(
        "Point alerts",
        f"{point_alert_count:,}",
    )
    metric_columns[1].metric(
        "Corroborated alerts",
        f"{corroborated_alert_count:,}",
    )
    metric_columns[2].metric(
        "Isolated alerts",
        f"{isolated_alert_count:,}",
    )
    metric_columns[3].metric(
        "Priority areas",
        f"{investigation_cluster_count:,}",
    )

    st.caption(
        f"Analysed {len(observations):,} synthetic "
        "drive-test observations."
    )

    (
        map_tab,
        investigation_tab,
        evidence_tab,
        governance_tab,
    ) = st.tabs(
        [
            "Investigation map",
            "Priority queue",
            "Threat evidence",
            "Governance and limitations",
        ]
    )

    with map_tab:
        st.markdown(
            "### Spatial alert corroboration"
        )
        st.write(
            "Use the layer control in the upper-right "
            "corner of the map to show or hide routes, "
            "stations, isolated alerts and investigation "
            "zones."
        )

        investigation_map = build_map(
            observations,
            cluster_summary,
        )
        st_folium(
            investigation_map,
            width=1200,
            height=650,
            returned_objects=[],
        )

    with investigation_tab:
        st.markdown(
            "### Prioritised investigation areas"
        )

        if cluster_summary.empty:
            st.success(
                "No spatially corroborated priority "
                "areas were found."
            )
        else:
            display_summary = (
                cluster_summary.copy(deep=True)
            )
            display_summary["priority"] = (
                display_summary["cluster_id"]
                .astype(int)
                + 1
            )
            display_summary = display_summary.rename(
                columns={
                    "observation_count": (
                        "corroborated_alerts"
                    ),
                    "dominant_cell_id": (
                        "reported_cell_id"
                    ),
                    "mean_threat_score": (
                        "mean_score"
                    ),
                    "maximum_threat_score": (
                        "maximum_score"
                    ),
                    "centroid_latitude": "latitude",
                    "centroid_longitude": "longitude",
                }
            )

            st.dataframe(
                display_summary[
                    [
                        "priority",
                        "reported_cell_id",
                        "corroborated_alerts",
                        "mean_score",
                        "maximum_score",
                        "latitude",
                        "longitude",
                        "start_time",
                        "end_time",
                    ]
                ],
                hide_index=True,
                width="stretch",
            )

            st.warning(
                "Recommended response: validate the "
                "reference-cell configuration, review "
                "neighbour-cell measurements, and conduct "
                "authorised passive RF surveying within "
                "the prioritised area."
            )

    with evidence_tab:
        st.markdown(
            "### Why was this area prioritised?"
        )
        st.write(
            "The evidence below compares the suspicious "
            "cluster with the central 98% range observed "
            "in normal synthetic measurements."
        )

        if cluster_summary.empty:
            st.success(
                "No investigation cluster is available "
                "for explanation."
            )
        elif diagnostics.empty:
            st.warning(
                "No feature diagnostics are available."
            )
        else:
            priority_options = sorted(
                (
                    diagnostics["cluster_id"]
                    .astype(int)
                    + 1
                ).unique()
            )

            selected_priority = st.selectbox(
                "Investigation priority",
                options=priority_options,
                format_func=lambda value: (
                    f"Priority area {value}"
                ),
            )
            selected_cluster_id = (
                int(selected_priority) - 1
            )

            cluster_evidence = diagnostics.loc[
                diagnostics["cluster_id"].astype(
                    int
                )
                == selected_cluster_id
            ].copy()

            feature_information = {
                "neighbour_count": {
                    "label": "Neighbour-cell count",
                    "unit": "cells",
                    "interpretation": (
                        "Unusually few neighbouring cells "
                        "were observed."
                    ),
                },
                "rsrp_residual_db": {
                    "label": "RSRP residual",
                    "unit": "dB",
                    "interpretation": (
                        "The received signal was much "
                        "stronger than expected for the "
                        "reported cell distance."
                    ),
                },
                "signal_distance_inconsistency": {
                    "label": (
                        "Signal-distance inconsistency"
                    ),
                    "unit": "derived score",
                    "interpretation": (
                        "Strong measurements occurred far "
                        "from the reported reference-cell "
                        "location."
                    ),
                },
            }

            evidence_rows: list[
                dict[str, object]
            ] = []

            for (
                feature_name,
                feature_details,
            ) in feature_information.items():
                matching_rows = (
                    cluster_evidence.loc[
                        cluster_evidence["feature"]
                        == feature_name
                    ]
                )

                if matching_rows.empty:
                    continue

                evidence = matching_rows.iloc[0]
                normal_minimum = float(
                    evidence["normal_p01"]
                )
                normal_maximum = float(
                    evidence["normal_p99"]
                )
                observed_median = float(
                    evidence["cluster_median"]
                )

                evidence_rows.append(
                    {
                        "Evidence": (
                            feature_details["label"]
                        ),
                        "Normal 98% range": (
                            f"{normal_minimum:.2f} to "
                            f"{normal_maximum:.2f}"
                        ),
                        "Cluster median": (
                            f"{observed_median:.2f}"
                        ),
                        "Unit": (
                            feature_details["unit"]
                        ),
                        "Interpretation": (
                            feature_details[
                                "interpretation"
                            ]
                        ),
                    }
                )

            if evidence_rows:
                st.dataframe(
                    pd.DataFrame(evidence_rows),
                    hide_index=True,
                    width="stretch",
                )
            else:
                st.warning(
                    "No selected evidence features were "
                    "found for this priority area."
                )

            st.warning(
                "These indicators establish measurement "
                "inconsistency, not malicious intent. "
                "Confirmation requires authorised technical "
                "investigation."
            )

        st.markdown(
            "### Synthetic benchmark"
        )
        st.caption(
            "Point-level performance on the controlled "
            "synthetic cloned-cell-style scenario only."
        )

        benchmark_columns = st.columns(4)

        benchmark_columns[0].metric(
            "Precision",
            (
                f"{evaluation_metrics['precision']:.1%}"
            ),
        )
        benchmark_columns[1].metric(
            "Recall",
            (
                f"{evaluation_metrics['recall']:.1%}"
            ),
        )
        benchmark_columns[2].metric(
            "F1 score",
            (
                f"{evaluation_metrics['f1_score']:.1%}"
            ),
        )
        benchmark_columns[3].metric(
            "False-positive rate",
            (
                f"{evaluation_metrics[
                    'false_positive_rate'
                ]:.2%}"
            ),
        )

        st.caption(
            "Spatial corroboration subsequently retained "
            "one 90-observation investigation cluster and "
            "treated all 14 false-positive point alerts as "
            "isolated noise."
        )

    with governance_tab:
        st.markdown(
            "### Responsible-use controls"
        )

        st.markdown(
            """
- All current observations and base stations are synthetic.
- The prototype stores no IMSI, IMEI, MSISDN, subscriber identity, payload or communications content.
- Threat scores prioritise observations for human review; they are not proof of malicious infrastructure.
- Field verification must be authorised and use lawful, passive measurement procedures.
- Real deployment would require calibrated devices, verified reference infrastructure and operator or regulator validation.
            """
        )

        st.markdown(
            "### Current limitations"
        )

        st.markdown(
            """
- Performance metrics and attack behaviour are simulated.
- The benchmark covers one cloned-cell-style geographic inconsistency scenario.
- Model performance on synthetic data does not establish real-world accuracy.
- Coverage propagation is simplified and does not fully model terrain, buildings, antenna patterns or network optimisation.
- Isolated alerts are retained for audit but are not escalated without spatial corroboration.
            """
        )


if __name__ == "__main__":
    main()