"""Interactive CellDefense GeoAI investigation dashboard."""

import json
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from shapely import wkt
from shapely.geometry import LineString

from celldefense.config import CYBERJAYA_AOI
from celldefense.network import (
    SYNTHETIC_BASE_STATIONS,
)

STYLES_PATH = Path(__file__).with_name(
    "styles.css"
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
RESPONSE_PLAN_PATH = (
    Path("data")
    / "processed"
    / "response_route_plan.csv"
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
def load_dashboard_styles() -> None:
    """Load the shared CellDefense dashboard stylesheet."""

    if not STYLES_PATH.exists():
        raise FileNotFoundError(
            f"Dashboard stylesheet not found: "
            f"{STYLES_PATH}"
        )

    stylesheet = STYLES_PATH.read_text(
        encoding="utf-8"
    )

    st.markdown(
        f"<style>{stylesheet}</style>",
        unsafe_allow_html=True,
    )
    
def load_dashboard_data() -> tuple[
    pd.DataFrame,
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
        
    if not RESPONSE_PLAN_PATH.exists():
        raise FileNotFoundError(
            "The response plan is missing. Run "
            "'python scripts/plan_response_routes.py' first."
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
    response_plan = pd.read_csv(
        RESPONSE_PLAN_PATH
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
        response_plan,
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
                    "<br>Decision: not spatio-temporally corroborated"
                ),
                max_width=280,
            ),
        ).add_to(noise_layer)

    noise_layer.add_to(map_object)


def add_response_routes(
    map_object: folium.Map,
    response_plan: pd.DataFrame,
) -> None:
    """Add fictional supporting access plans to the map."""

    route_layer = folium.FeatureGroup(
        name="Synthetic response access plan",
        show=True,
    )

    for plan in response_plan.itertuples():
        response_path = wkt.loads(
            plan.path_wkt
        )

        if not isinstance(
            response_path,
            LineString,
        ):
            raise ValueError(
                "Response path must be a LineString."
            )

        path_coordinates = [
            (latitude, longitude)
            for longitude, latitude
            in response_path.coords
        ]

        folium.PolyLine(
            locations=path_coordinates,
            color="#1565c0",
            weight=5,
            opacity=0.9,
            tooltip=(
                f"Priority {int(plan.priority_rank)} "
                "synthetic access plan"
            ),
            popup=folium.Popup(
                (
                    "<strong>Synthetic access plan</strong>"
                    f"<br>Priority: "
                    f"{int(plan.priority_rank)}"
                    f"<br>Route: {plan.route_id}"
                    f"<br>Staging endpoint: "
                    f"{plan.staging_endpoint}"
                    f"<br>Route distance: "
                    f"{plan.route_distance_m / 1000:.2f} km"
                    f"<br>Off-route distance: "
                    f"{plan.off_route_distance_m:.1f} m"
                    "<br><em>Not suitable for real "
                    "navigation.</em>"
                ),
                max_width=320,
            ),
        ).add_to(route_layer)

        folium.CircleMarker(
            location=[
                plan.staging_latitude,
                plan.staging_longitude,
            ],
            radius=7,
            color="#0d47a1",
            weight=2,
            fill=True,
            fill_color="#1565c0",
            fill_opacity=1.0,
            tooltip=(
                "Fictional response staging point"
            ),
            popup=(
                f"Priority {int(plan.priority_rank)} "
                "fictional staging point"
            ),
        ).add_to(route_layer)

        folium.CircleMarker(
            location=[
                plan.access_latitude,
                plan.access_longitude,
            ],
            radius=7,
            color="#1b5e20",
            weight=2,
            fill=True,
            fill_color="#43a047",
            fill_opacity=1.0,
            tooltip=(
                "Nearest synthetic route access point"
            ),
            popup=(
                f"Priority {int(plan.priority_rank)} "
                "synthetic access point"
            ),
        ).add_to(route_layer)

    route_layer.add_to(map_object)


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
            cluster.priority_rank
        )

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
    response_plan: pd.DataFrame,
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
    add_response_routes(
        map_object,
        response_plan,
    )
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


def render_dashboard_header() -> None:
    """Render the shared dashboard identity and safeguards."""

    st.markdown(
        """
        <section class="cd-hero">
            <div class="cd-hero-content">
                <div>
                    <h1 class="cd-brand-title">
                        CellDefense GeoAI
                    </h1>
                    <p class="cd-brand-subtitle">
                        Cellular anomaly triage and field
                        investigation support
                    </p>
                    <p class="cd-hero-statement">
                        From cellular measurement anomalies to
                        prioritised investigation decisions.
                    </p>
                    <div class="cd-workflow">
                        Detect → Corroborate → Prioritise → Review
                    </div>
                </div>
                <div class="cd-badges">
                    <span class="cd-badge">
                        Synthetic pilot
                    </span>
                    <span class="cd-badge">
                        Cyberjaya
                    </span>
                    <span class="cd-badge">
                        Decision support
                    </span>
                </div>
            </div>
        </section>

        <section class="cd-safeguard">
            <div class="cd-eyebrow">
                Decision-support safeguard
            </div>
            <p>
                The system identifies suspicious measurement
                inconsistencies. It does not confirm a rogue base
                station or establish malicious intent.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(
        "How to use this dashboard",
        expanded=False,
    ):
        st.markdown(
            """
            1. Start with **Threat Overview** to locate
               suspicious activity.
            2. Use **Priority Queue** to identify the first
               investigation area.
            3. Review **Threat Evidence** to understand why
               the area was prioritised.
            4. Use **Response Plan** to inspect the synthetic
               field-access plan.
            5. Check **Responsible Use** before interpreting
               or presenting the result.
            """
        )


def render_summary_cards(
    point_alert_count: int,
    corroborated_alert_count: int,
    isolated_alert_count: int,
    investigation_cluster_count: int,
    observation_count: int,
) -> None:
    """Render operational summary cards."""

    summary_html = (
        '<section class="cd-kpi-grid">'
        '<article class="cd-kpi">'
        '<div class="cd-kpi-label">'
        'Suspicious observations'
        '</div>'
        '<div class="cd-kpi-value">'
        f'{point_alert_count:,}'
        '</div>'
        '<div class="cd-kpi-description">'
        'Flagged for analyst review'
        '</div>'
        '</article>'
        '<article class="cd-kpi cd-kpi--red">'
        '<div class="cd-kpi-label">'
        'Corroborated alerts'
        '</div>'
        '<div class="cd-kpi-value">'
        f'{corroborated_alert_count:,}'
        '</div>'
        '<div class="cd-kpi-description">'
        'Supported by nearby observations'
        '</div>'
        '</article>'
        '<article class="cd-kpi cd-kpi--amber">'
        '<div class="cd-kpi-label">'
        'Isolated alerts'
        '</div>'
        '<div class="cd-kpi-value">'
        f'{isolated_alert_count:,}'
        '</div>'
        '<div class="cd-kpi-description">'
        'Retained, but not escalated'
        '</div>'
        '</article>'
        '<article class="cd-kpi cd-kpi--red">'
        '<div class="cd-kpi-label">'
        'Priority areas'
        '</div>'
        '<div class="cd-kpi-value">'
        f'{investigation_cluster_count:,}'
        '</div>'
        '<div class="cd-kpi-description">'
        'Require authorised review'
        '</div>'
        '</article>'
        '</section>'
        '<div class="cd-observation-caption">'
        'Analysed observations: '
        f'{observation_count:,} '
        'synthetic drive-test measurements.'
        '</div>'
    )

    st.markdown(
        summary_html,
        unsafe_allow_html=True,
    )
    
    
def render_priority_overview(
    cluster_summary: pd.DataFrame,
) -> None:
    """Render the highest-priority investigation summary."""

    if cluster_summary.empty:
        st.success(
            "No spatially corroborated priority areas "
            "were found."
        )
        return

    priority_area = cluster_summary.sort_values(
        by="priority_rank",
        ascending=True,
    ).iloc[0]

    start_time = pd.Timestamp(
        priority_area["start_time"]
    )
    end_time = pd.Timestamp(
        priority_area["end_time"]
    )

    duration_seconds = max(
        0,
        int(
            (
                end_time - start_time
            ).total_seconds()
        ),
    )
    duration_minutes, remaining_seconds = divmod(
        duration_seconds,
        60,
    )
    duration_text = (
        f"{duration_minutes} min "
        f"{remaining_seconds} sec"
    )

    timezone_text = start_time.strftime("%z")
    if len(timezone_text) == 5:
        timezone_text = (
            f"{timezone_text[:3]}:"
            f"{timezone_text[3:]}"
        )

    detection_window = (
        f"{start_time.strftime('%d %b %Y')}, "
        f"{start_time.strftime('%H:%M:%S')}–"
        f"{end_time.strftime('%H:%M:%S')} "
        f"{timezone_text}"
    )

    priority_rank = int(
        priority_area["priority_rank"]
    )
    observation_count = int(
        priority_area["observation_count"]
    )
    reported_cell_id = str(
        priority_area["dominant_cell_id"]
    )
    latitude = float(
        priority_area["centroid_latitude"]
    )
    longitude = float(
        priority_area["centroid_longitude"]
    )
    priority_score = float(
        priority_area["maximum_threat_score"]
    )

    if priority_score.is_integer():
        score_text = str(int(priority_score))
    else:
        score_text = f"{priority_score:.1f}"

    panel_html = (
        '<section class="cd-priority-panel">'
        '<div class="cd-priority-panel-header">'
        '<div class="cd-priority-status">'
        '<span class="cd-priority-status-dot"></span>'
        'Investigation review required'
        '</div>'
        '<h3>'
        f'Priority Area {priority_rank}'
        '</h3>'
        '<p>'
        f'{observation_count:,} corroborated observations '
        f'associated with reported {reported_cell_id}.'
        '</p>'
        '</div>'
        '<div class="cd-priority-panel-body">'
        '<div class="cd-detail-grid">'
        '<div>'
        '<div class="cd-detail-label">'
        'Reported cell'
        '</div>'
        '<div class="cd-detail-value">'
        f'{reported_cell_id}'
        '</div>'
        '</div>'
        '<div>'
        '<div class="cd-detail-label">'
        'Corroborated observations'
        '</div>'
        '<div class="cd-detail-value">'
        f'{observation_count:,}'
        '</div>'
        '</div>'
        '<div>'
        '<div class="cd-detail-label">'
        'Detection window'
        '</div>'
        '<div class="cd-detail-value">'
        f'{detection_window}'
        '</div>'
        '</div>'
        '<div>'
        '<div class="cd-detail-label">'
        'Observed duration'
        '</div>'
        '<div class="cd-detail-value">'
        f'{duration_text}'
        '</div>'
        '</div>'
        '</div>'
        '<div class="cd-location-box">'
        '<div class="cd-detail-label">'
        'Estimated cluster centre'
        '</div>'
        '<div class="cd-detail-value">'
        f'{latitude:.5f}, {longitude:.5f}'
        '</div>'
        '</div>'
        '<div class="cd-priority-score">'
        '<div>'
        '<div class="cd-detail-label">'
        'Investigation priority score'
        '</div>'
        '<div class="cd-kpi-description">'
        'Relative anomaly score for prioritisation; '
        'not a probability.'
        '</div>'
        '</div>'
        '<div class="cd-score-number">'
        f'{score_text}'
        '<span class="cd-score-denominator">'
        '/100'
        '</span>'
        '</div>'
        '</div>'
        '<div class="cd-why-box">'
        '<div class="cd-detail-label">'
        'Why this matters'
        '</div>'
        '<p>'
        'Multiple unusual measurements occurred close '
        'together in space and time while reporting the '
        'same cell identity.'
        '</p>'
        '</div>'
        '<div class="cd-next-step">'
        '<div class="cd-detail-label">'
        'Recommended next step'
        '</div>'
        '<p>'
        'Review the threat evidence, validate reference-cell '
        'configuration and plan an authorised passive RF '
        'survey if further investigation is warranted.'
        '</p>'
        '</div>'
        '</div>'
        '</section>'
    )

    st.markdown(
        panel_html,
        unsafe_allow_html=True,
    )


def main() -> None:
    """Render the CellDefense dashboard."""

    st.set_page_config(
        page_title="CellDefense GeoAI",
        page_icon="🖥️",
        layout="wide",
    )
    
    load_dashboard_styles()
    render_dashboard_header()

    try:
        (
            observations,
            cluster_summary,
            diagnostics,
            response_plan,
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

    render_summary_cards(
        point_alert_count=point_alert_count,
        corroborated_alert_count=(
            corroborated_alert_count
        ),
        isolated_alert_count=isolated_alert_count,
        investigation_cluster_count=(
            investigation_cluster_count
        ),
        observation_count=len(observations),
    )

    (
        map_tab,
        investigation_tab,
        evidence_tab,
        response_tab,
        governance_tab,
    ) = st.tabs(
        [
            "Threat Overview",
            "Priority Queue",
            "Threat Evidence",
            "Response Plan",
            "Responsible Use",
        ]
    )

    with map_tab:
        st.markdown(
            (
                '<section class="cd-section-heading">'
                '<div class="cd-eyebrow">'
                'Threat Overview'
                '</div>'
                '<h2>'
                'What is happening and where?'
                '</h2>'
                '<p>'
                'Priority areas indicate where authorised '
                'follow-up should begin. They identify '
                'spatio-temporally corroborated measurement '
                'inconsistencies and do not establish '
                'malicious activity.'
                '</p>'
                '</section>'
            ),
            unsafe_allow_html=True,
        )

        overview_columns = st.columns(
            [2.15, 1],
            gap="large",
        )

        with overview_columns[0]:
            st.caption(
                "Use the map layer control to show or hide "
                "synthetic routes, reference stations, "
                "isolated alerts, corroborated alerts and "
                "investigation zones."
            )

            investigation_map = build_map(
                observations,
                cluster_summary,
                response_plan,
            )
            st_folium(
                investigation_map,
                width=900,
                height=650,
                returned_objects=[],
            )

        with overview_columns[1]:
            render_priority_overview(
                cluster_summary
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
                display_summary["priority_rank"]
                .astype(int)
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

    with response_tab:
        st.markdown(
            "### Supporting field-access plan"
        )
        st.write(
            "For each priority area, the prototype finds "
            "the nearest fictional route, projects an "
            "access point onto it, and selects the shorter "
            "path from either route endpoint."
        )

        if response_plan.empty:
            st.success(
                "No response access plan is required."
            )
        else:
            response_display = response_plan.copy(
                deep=True
            )
            response_display[
                "route_distance_km"
            ] = (
                response_display[
                    "route_distance_m"
                ]
                / 1000
            ).round(2)
            response_display[
                "off_route_distance_m"
            ] = response_display[
                "off_route_distance_m"
            ].round(1)

            response_display = (
                response_display.rename(
                    columns={
                        "priority_rank": "priority",
                        "route_id": (
                            "synthetic_route"
                        ),
                        "staging_endpoint": (
                            "selected_endpoint"
                        ),
                        "staging_latitude": (
                            "staging_lat"
                        ),
                        "staging_longitude": (
                            "staging_lon"
                        ),
                        "access_latitude": (
                            "access_lat"
                        ),
                        "access_longitude": (
                            "access_lon"
                        ),
                    }
                )
            )

            st.dataframe(
                response_display[
                    [
                        "priority",
                        "synthetic_route",
                        "selected_endpoint",
                        "route_distance_km",
                        "off_route_distance_m",
                        "staging_lat",
                        "staging_lon",
                        "access_lat",
                        "access_lon",
                    ]
                ],
                hide_index=True,
                width="stretch",
            )

            first_plan = response_plan.sort_values(
                by="priority_rank"
            ).iloc[0]

            response_metrics = st.columns(3)

            response_metrics[0].metric(
                "Selected synthetic route",
                first_plan["route_id"],
            )
            response_metrics[1].metric(
                "Route distance",
                (
                    f"{first_plan[
                        'route_distance_m'
                    ] / 1000:.2f} km"
                ),
            )
            response_metrics[2].metric(
                "Off-route distance",
                (
                    f"{first_plan[
                        'off_route_distance_m'
                    ]:.1f} m"
                ),
            )

            st.info(
                "Method: select the geographically nearest "
                "synthetic route, then minimise distance "
                "from either fictional route endpoint to "
                "the projected access point."
            )

        st.warning(
            "This access plan uses fictional drive routes. "
            "It is a supporting demonstration and must not "
            "be used for real navigation or deployment."
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
            cluster_by_priority = {
                int(cluster.priority_rank): int(
                    cluster.cluster_id
                )
                for cluster in cluster_summary.itertuples()
            }
            priority_options = sorted(
                cluster_by_priority
            )

            selected_priority = st.selectbox(
                "Investigation priority",
                options=priority_options,
                format_func=lambda value: (
                    f"Priority area {value}"
                ),
            )
            selected_cluster_id = (
                cluster_by_priority[
                    int(selected_priority)
                ]
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
            "Spatio-temporal corroboration subsequently retained "
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
- Isolated alerts are retained for audit but are not escalated without spatio-temporal corroboration.
- The supporting response plan uses fictional drive routes rather than a verified road network and is not suitable for real navigation.
            """
        )


if __name__ == "__main__":
    main()