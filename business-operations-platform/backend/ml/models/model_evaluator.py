import numpy as np
import pandas as pd

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)


def assess_data_sufficiency(
    y,
    minimum_observations=14,
):
    """
    Assess whether the target series contains enough useful
    information for forecasting.
    """

    y = pd.Series(y).dropna()

    observations = len(y)
    unique_values = y.nunique()

    if observations == 0:
        return {
            "status": "insufficient",
            "reason": "No usable target observations.",
            "observations": 0,
            "unique_values": 0,
            "has_variation": False,
        }

    if observations < minimum_observations:
        return {
            "status": "insufficient",
            "reason": (
                f"Only {observations} observations are available; "
                f"at least {minimum_observations} are required."
            ),
            "observations": observations,
            "unique_values": unique_values,
            "has_variation": unique_values > 1,
        }

    if unique_values <= 1:
        return {
            "status": "low_variation",
            "reason": (
                "The target contains no meaningful variation."
            ),
            "observations": observations,
            "unique_values": unique_values,
            "has_variation": False,
        }

    return {
        "status": "sufficient",
        "reason": None,
        "observations": observations,
        "unique_values": unique_values,
        "has_variation": True,
    }


def calculate_forecast_metrics(
    y_true,
    y_pred,
):
    """
    Calculate regression metrics safely.
    """

    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    mae = mean_absolute_error(
        y_true,
        y_pred,
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_true,
            y_pred,
        )
    )

    r2 = r2_score(
        y_true,
        y_pred,
    )

    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "r2": float(r2),
    }


def calculate_baseline_metrics(
    y_train,
    y_test,
):
    """
    Evaluate a historical-mean baseline.
    """

    y_train = pd.Series(y_train)
    y_test = pd.Series(y_test)

    baseline_value = y_train.mean()

    predictions = np.full(
        len(y_test),
        baseline_value,
    )

    return {
        "baseline_value": float(baseline_value),
        **calculate_forecast_metrics(
            y_test,
            predictions,
        ),
    }


def evaluate_model_against_baseline(
    y_test,
    predictions,
    baseline_metrics,
):
    """
    Compare a model against the historical-mean baseline.
    """

    model_metrics = calculate_forecast_metrics(
        y_test,
        predictions,
    )

    baseline_rmse = baseline_metrics["rmse"]
    model_rmse = model_metrics["rmse"]

    if baseline_rmse == 0:
        improvement = 0.0
    else:
        improvement = (
            (baseline_rmse - model_rmse)
            / baseline_rmse
        ) * 100

    model_metrics["baseline_rmse"] = float(
        baseline_rmse
    )

    model_metrics[
        "improvement_vs_baseline_percent"
    ] = float(improvement)

    model_metrics["beats_baseline"] = (
        model_rmse < baseline_rmse
    )

    return model_metrics


def assess_validation_strength(
    y_test,
    metrics,
):
    """
    Assess how much evidence the validation result provides.

    A small validation set or a perfect score should not
    automatically be interpreted as strong evidence.
    """

    validation_observations = len(y_test)

    warnings = []

    if validation_observations < 10:
        warnings.append(
            "Validation set contains fewer than 10 observations."
        )

    if validation_observations < 20:
        warnings.append(
            "Validation evidence is limited because the "
            "validation set is relatively small."
        )

    if (
        metrics["rmse"] == 0
        and metrics["mae"] == 0
    ):
        warnings.append(
            "The model produced a perfect validation score. "
            "This may indicate an overly simple or very small "
            "validation problem and should not be interpreted "
            "as proof of perfect future accuracy."
        )

    if metrics["r2"] >= 0.99:
        warnings.append(
            "Validation R² is extremely high. Additional "
            "historical data is required before treating "
            "the forecast as highly reliable."
        )

    return {
        "validation_observations": validation_observations,
        "warnings": warnings,
    }


def determine_reliability(
    data_assessment,
    metrics,
    validation_strength,
):
    """
    Determine conservative forecast reliability.
    """

    if data_assessment["status"] == "insufficient":
        return {
            "level": "insufficient",
            "reason": data_assessment["reason"],
        }

    if not data_assessment["has_variation"]:
        return {
            "level": "low",
            "reason": (
                "The target has insufficient variation "
                "for meaningful forecasting."
            ),
        }

    if not metrics.get("beats_baseline", False):
        return {
            "level": "low",
            "reason": (
                "The selected model does not outperform "
                "the historical baseline."
            ),
        }

    warnings = validation_strength["warnings"]

    if (
        metrics["rmse"] == 0
        and metrics["mae"] == 0
    ):
        return {
            "level": "low",
            "reason": (
                "The model achieved a perfect validation "
                "score, but the available validation evidence "
                "is too limited to establish strong reliability."
            ),
        }

    if len(warnings) >= 2:
        return {
            "level": "low",
            "reason": (
                "The model beats the baseline, but validation "
                "evidence is limited."
            ),
        }

    improvement = metrics.get(
        "improvement_vs_baseline_percent",
        0,
    )

    if improvement >= 30:
        return {
            "level": "moderate",
            "reason": (
                "The model materially improves on the baseline, "
                "but additional historical data would increase "
                "confidence."
            ),
        }

    return {
        "level": "low",
        "reason": (
            "The model provides some improvement over the "
            "baseline, but the evidence is not strong enough "
            "for high-confidence forecasting."
        ),
    }