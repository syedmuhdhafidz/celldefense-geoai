"""Unsupervised anomaly detection for CellDefense GeoAI."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    f1_score,
    precision_score,
    recall_score,
)

from celldefense.config import DEFAULT_RANDOM_SEED
from celldefense.features import MODEL_FEATURE_COLUMNS


@dataclass(frozen=True, slots=True)
class TrainedAnomalyDetector:
    """Isolation Forest and its baseline-derived score thresholds."""

    model: IsolationForest
    alert_threshold: float
    score_floor: float
    score_ceiling: float


def train_anomaly_detector(
    baseline_features: pd.DataFrame,
    target_false_positive_rate: float = 0.01,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> TrainedAnomalyDetector:
    """Train an Isolation Forest using normal observations only."""

    if baseline_features.empty:
        raise ValueError(
            "Baseline feature data must not be empty."
        )

    if baseline_features["is_anomaly"].any():
        raise ValueError(
            "Training data must contain baseline "
            "observations only."
        )

    if not 0.0 < target_false_positive_rate < 0.5:
        raise ValueError(
            "target_false_positive_rate must be "
            "between 0 and 0.5."
        )

    model_input = baseline_features[
        MODEL_FEATURE_COLUMNS
    ].to_numpy(dtype=float)

    if not np.isfinite(model_input).all():
        raise ValueError(
            "Model features must contain only finite values."
        )

    model = IsolationForest(
        n_estimators=300,
        contamination="auto",
        random_state=random_seed,
        n_jobs=-1,
    )
    model.fit(model_input)

    baseline_raw_scores = -model.score_samples(
        model_input
    )

    alert_threshold = float(
        np.quantile(
            baseline_raw_scores,
            1.0 - target_false_positive_rate,
        )
    )
    score_floor = float(
        np.quantile(
            baseline_raw_scores,
            0.50,
        )
    )
    score_ceiling = float(
        np.quantile(
            baseline_raw_scores,
            0.995,
        )
    )

    if score_ceiling <= score_floor:
        score_ceiling = score_floor + 1e-9

    return TrainedAnomalyDetector(
        model=model,
        alert_threshold=alert_threshold,
        score_floor=score_floor,
        score_ceiling=score_ceiling,
    )


def score_feature_table(
    detector: TrainedAnomalyDetector,
    features: pd.DataFrame,
) -> pd.DataFrame:
    """Add raw anomaly, threat, and alert fields to a feature table."""

    if features.empty:
        raise ValueError(
            "Feature data to score must not be empty."
        )

    model_input = features[
        MODEL_FEATURE_COLUMNS
    ].to_numpy(dtype=float)

    if not np.isfinite(model_input).all():
        raise ValueError(
            "Model features must contain only finite values."
        )

    raw_scores = -detector.model.score_samples(
        model_input
    )

    threat_scores = (
        (
            raw_scores - detector.score_floor
        )
        / (
            detector.score_ceiling
            - detector.score_floor
        )
    ) * 100.0

    bounded_threat_scores = np.clip(
        threat_scores,
        0.0,
        100.0,
    )
    predicted_anomalies = (
        raw_scores >= detector.alert_threshold
    )

    result = features.copy(deep=True)
    result["raw_anomaly_score"] = np.round(
        raw_scores,
        6,
    )
    result["threat_score"] = np.round(
        bounded_threat_scores,
        2,
    )
    result["predicted_anomaly"] = (
        predicted_anomalies.astype(bool)
    )

    return result


def evaluate_predictions(
    scored_features: pd.DataFrame,
) -> dict[str, float]:
    """Evaluate alert predictions against synthetic labels."""

    required_columns = {
        "is_anomaly",
        "predicted_anomaly",
    }
    missing_columns = required_columns - set(
        scored_features.columns
    )
    if missing_columns:
        raise ValueError(
            f"Missing evaluation columns: "
            f"{sorted(missing_columns)}"
        )

    true_labels = scored_features[
        "is_anomaly"
    ].astype(bool)
    predictions = scored_features[
        "predicted_anomaly"
    ].astype(bool)

    true_negatives = int(
        ((~true_labels) & (~predictions)).sum()
    )
    false_positives = int(
        ((~true_labels) & predictions).sum()
    )

    negative_count = (
        true_negatives + false_positives
    )
    false_positive_rate = (
        false_positives / negative_count
        if negative_count
        else 0.0
    )

    return {
        "precision": float(
            precision_score(
                true_labels,
                predictions,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                true_labels,
                predictions,
                zero_division=0,
            )
        ),
        "f1_score": float(
            f1_score(
                true_labels,
                predictions,
                zero_division=0,
            )
        ),
        "false_positive_rate": float(
            false_positive_rate
        ),
    }