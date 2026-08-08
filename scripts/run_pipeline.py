"""Run the complete CellDefense synthetic GeoAI pipeline."""

from collections.abc import Callable

from cluster_alerts import main as cluster_alerts
from diagnose_clusters import main as diagnose_clusters
from generate_baseline import main as generate_baseline
from generate_scenario_dataset import (
    main as generate_scenario_dataset,
)
from plot_baseline import main as plot_baseline
from plot_detection_results import (
    main as plot_detection_results,
)
from plot_scenario import main as plot_scenario
from train_detector import main as train_detector

PipelineStage = tuple[str, Callable[[], None]]

PIPELINE_STAGES: list[PipelineStage] = [
    (
        "Generate synthetic baseline observations",
        generate_baseline,
    ),
    (
        "Generate cloned-cell-style scenario",
        generate_scenario_dataset,
    ),
    (
        "Train and evaluate anomaly detector",
        train_detector,
    ),
    (
        "Perform cell-aware spatial corroboration",
        cluster_alerts,
    ),
    (
        "Generate cluster diagnostics",
        diagnose_clusters,
    ),
    (
        "Plot baseline network",
        plot_baseline,
    ),
    (
        "Plot injected scenario",
        plot_scenario,
    ),
    (
        "Plot detection results",
        plot_detection_results,
    ),
]


def main() -> None:
    """Execute all pipeline stages in dependency order."""

    print("Starting the CellDefense GeoAI pipeline")
    print(
        f"Pipeline stages: {len(PIPELINE_STAGES)}"
    )
    print("")

    for stage_number, (
        stage_name,
        stage_function,
    ) in enumerate(
        PIPELINE_STAGES,
        start=1,
    ):
        print(
            f"[{stage_number}/{len(PIPELINE_STAGES)}] "
            f"{stage_name}"
        )
        stage_function()
        print("")

    print(
        "CellDefense GeoAI pipeline completed "
        "successfully"
    )
    print(
        "Launch the dashboard with: "
        "python -m streamlit run dashboard/app.py"
    )


if __name__ == "__main__":
    main()