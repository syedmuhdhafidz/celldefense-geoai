"""Train and evaluate the CellDefense anomaly detector."""

import json
from pathlib import Path

import joblib

from celldefense.anomalies import inject_cloned_cell
from celldefense.features import build_feature_table
from celldefense.generator import (
    generate_baseline_observations,
)
from celldefense.model import (
    evaluate_predictions,
    score_feature_table,
    train_anomaly_detector,
)


OUTPUT_DIRECTORY = Path("data") / "processed"
MODEL_OUTPUT_PATH = (
    OUTPUT_DIRECTORY / "anomaly_detector.joblib"
)
SCORED_PARQUET_PATH = (
    OUTPUT_DIRECTORY / "scored_observations.parquet"
)
SCORED_CSV_PATH = (
    OUTPUT_DIRECTORY / "scored_observations.csv"
)
METRICS_OUTPUT_PATH = (
    OUTPUT_DIRECTORY / "evaluation_metrics.json"
)


def main() -> None:
    """Execute the complete training and evaluation workflow."""

    OUTPUT_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    training_observations = (
        generate_baseline_observations(
            samples_per_route=600,
            random_seed=2026,
        )
    )
    scenario_baseline = (
        generate_baseline_observations(
            samples_per_route=600,
            random_seed=3030,
        )
    )
    scenario_observations = inject_cloned_cell(
        observations=scenario_baseline,
        route_id="route-west-east",
        cloned_cell_id="cell-001",
        start_fraction=0.55,
        end_fraction=0.70,
        random_seed=4040,
    )

    training_features = build_feature_table(
        training_observations
    )
    scenario_features = build_feature_table(
        scenario_observations
    )

    detector = train_anomaly_detector(
        baseline_features=training_features,
        target_false_positive_rate=0.01,
        random_seed=2026,
    )
    scored_observations = score_feature_table(
        detector=detector,
        features=scenario_features,
    )
    metrics = evaluate_predictions(
        scored_observations
    )

    true_labels = scored_observations[
        "is_anomaly"
    ].astype(bool)
    predictions = scored_observations[
        "predicted_anomaly"
    ].astype(bool)

    true_positives = int(
        (true_labels & predictions).sum()
    )
    false_positives = int(
        ((~true_labels) & predictions).sum()
    )
    true_negatives = int(
        ((~true_labels) & (~predictions)).sum()
    )
    false_negatives = int(
        (true_labels & (~predictions)).sum()
    )

    baseline_scores = scored_observations.loc[
        ~scored_observations["is_anomaly"],
        "threat_score",
    ]
    anomaly_scores = scored_observations.loc[
        scored_observations["is_anomaly"],
        "threat_score",
    ]

    output_metrics = {
        **metrics,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "true_negatives": true_negatives,
        "false_negatives": false_negatives,
        "training_observations": len(
            training_observations
        ),
        "scenario_observations": len(
            scenario_observations
        ),
        "synthetic_anomalies": int(
            true_labels.sum()
        ),
        "median_baseline_threat_score": float(
            baseline_scores.median()
        ),
        "median_anomaly_threat_score": float(
            anomaly_scores.median()
        ),
    }

    joblib.dump(
        detector,
        MODEL_OUTPUT_PATH,
    )
    scored_observations.to_parquet(
        SCORED_PARQUET_PATH,
        index=False,
    )
    scored_observations.to_csv(
        SCORED_CSV_PATH,
        index=False,
    )
    METRICS_OUTPUT_PATH.write_text(
        json.dumps(
            output_metrics,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("CellDefense detection experiment complete")
    print(
        "Training observations: "
        f"{len(training_observations):,}"
    )
    print(
        "Scenario observations: "
        f"{len(scenario_observations):,}"
    )
    print(
        "Synthetic anomalies: "
        f"{int(true_labels.sum()):,}"
    )
    print("")
    print("Evaluation metrics")
    print(
        f"  Precision: "
        f"{metrics['precision']:.4f}"
    )
    print(
        f"  Recall: "
        f"{metrics['recall']:.4f}"
    )
    print(
        f"  F1 score: "
        f"{metrics['f1_score']:.4f}"
    )
    print(
        f"  False-positive rate: "
        f"{metrics['false_positive_rate']:.4f}"
    )
    print("")
    print("Confusion matrix")
    print(f"  True positives: {true_positives}")
    print(f"  False positives: {false_positives}")
    print(f"  True negatives: {true_negatives}")
    print(f"  False negatives: {false_negatives}")
    print("")
    print("Threat-score comparison")
    print(
        "  Median baseline score: "
        f"{baseline_scores.median():.2f}"
    )
    print(
        "  Median anomaly score: "
        f"{anomaly_scores.median():.2f}"
    )
    print("")
    print(f"Model: {MODEL_OUTPUT_PATH}")
    print(f"Scored data: {SCORED_PARQUET_PATH}")
    print(f"Metrics: {METRICS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()