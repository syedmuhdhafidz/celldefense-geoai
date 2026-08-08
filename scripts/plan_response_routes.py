"""Generate supporting access plans for priority areas."""

from pathlib import Path

import pandas as pd

from celldefense.routing import (
    plan_response_routes,
)

CLUSTER_SUMMARY_PATH = (
    Path("data")
    / "processed"
    / "alert_cluster_summary.csv"
)
OUTPUT_PATH = (
    Path("data")
    / "processed"
    / "response_route_plan.csv"
)


def main() -> None:
    """Generate and save synthetic response-route plans."""

    if not CLUSTER_SUMMARY_PATH.exists():
        raise FileNotFoundError(
            "The cluster summary is missing. Run "
            "'python scripts/cluster_alerts.py' first."
        )

    cluster_summary = pd.read_csv(
        CLUSTER_SUMMARY_PATH
    )
    response_plan = plan_response_routes(
        cluster_summary
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    response_plan.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print(
        "CellDefense supporting response planning "
        "complete"
    )
    print(
        "Priority areas planned: "
        f"{len(response_plan):,}"
    )

    if response_plan.empty:
        print(
            "No response routes were required."
        )
    else:
        display_columns = [
            "priority_rank",
            "route_id",
            "staging_endpoint",
            "route_distance_m",
            "off_route_distance_m",
        ]
        print("")
        print("Synthetic access-plan summary:")
        print(
            response_plan[
                display_columns
            ].to_string(index=False)
        )

    print("")
    print(
        "Response plan: "
        f"{OUTPUT_PATH}"
    )
    print(
        "Planning limitation: routes are fictional "
        "and are not suitable for real navigation."
    )


if __name__ == "__main__":
    main()