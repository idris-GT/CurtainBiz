import numpy as np

from ml.models.model_registry import get_regression_models
from ml.models.model_evaluator import (
    assess_data_sufficiency,
    calculate_forecast_metrics,
    evaluate_model_against_baseline,
    assess_validation_strength,
    determine_reliability,
)


# ==========================================================
# SIMPLE TIME-BASED SPLIT
# ==========================================================

def time_based_split(
    X,
    y,
    test_ratio=0.2,
):
    """
    Split time-ordered data without shuffling.

    Kept for compatibility with existing code.
    """

    if len(X) != len(y):
        raise ValueError(
            "X and y must contain the same number of rows."
        )

    if len(X) < 5:
        raise ValueError(
            "Not enough observations for time-based validation."
        )

    split_index = int(
        len(X) * (1 - test_ratio)
    )

    if split_index <= 0 or split_index >= len(X):
        raise ValueError(
            "Invalid validation split."
        )

    X_train = X.iloc[:split_index]
    X_test = X.iloc[split_index:]

    y_train = y.iloc[:split_index]
    y_test = y.iloc[split_index:]

    return (
        X_train,
        X_test,
        y_train,
        y_test,
    )


# ==========================================================
# WALK-FORWARD VALIDATION
# ==========================================================

def create_walk_forward_splits(
    X,
    y,
    n_splits=3,
    test_size=None,
):
    """
    Create expanding-window walk-forward validation splits.

    Example:

        Fold 1:
        TRAIN TRAIN TRAIN | TEST

        Fold 2:
        TRAIN TRAIN TRAIN TRAIN | TEST

        Fold 3:
        TRAIN TRAIN TRAIN TRAIN TRAIN | TEST

    No future observations are used to train earlier folds.
    """

    if len(X) != len(y):
        raise ValueError(
            "X and y must contain the same number of rows."
        )

    observations = len(X)

    if observations < 12:
        raise ValueError(
            "At least 12 observations are required "
            "for walk-forward validation."
        )

    # ------------------------------------------------------
    # DETERMINE TEST SIZE
    # ------------------------------------------------------

    if test_size is None:
        test_size = max(
            4,
            observations // 8,
        )

    # ------------------------------------------------------
    # DETERMINE MINIMUM TRAINING SIZE
    # ------------------------------------------------------

    required_training_size = max(
        10,
        observations // 3,
    )

    maximum_splits = (
        observations - required_training_size
    ) // test_size

    actual_splits = min(
        n_splits,
        maximum_splits,
    )

    if actual_splits < 2:
        raise ValueError(
            "Not enough observations for walk-forward validation."
        )

    splits = []

    # ------------------------------------------------------
    # KEEP THE VALIDATION WINDOWS AT THE END OF THE
    # HISTORICAL DATASET
    # ------------------------------------------------------

    first_test_start = (
        observations
        - actual_splits * test_size
    )

    for fold_number in range(
        actual_splits
    ):

        train_end = (
            first_test_start
            + fold_number * test_size
        )

        test_start = train_end

        test_end = (
            test_start
            + test_size
        )

        X_train = X.iloc[
            :train_end
        ]

        X_test = X.iloc[
            test_start:test_end
        ]

        y_train = y.iloc[
            :train_end
        ]

        y_test = y.iloc[
            test_start:test_end
        ]

        splits.append({
            "fold": fold_number + 1,
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
        })

    return splits


# ==========================================================
# BASELINE VALIDATION
# ==========================================================

def calculate_walk_forward_baseline(
    validation_splits,
):
    """
    Calculate the historical-mean baseline across all
    walk-forward validation periods.

    The baseline for each fold uses only that fold's
    training history.
    """

    all_actuals = []
    all_baseline_predictions = []

    fold_results = []

    for split in validation_splits:

        y_train = split["y_train"]
        y_test = split["y_test"]

        # Historical mean calculated ONLY from training data.
        baseline_value = float(
            y_train.mean()
        )

        baseline_predictions = np.full(
            len(y_test),
            baseline_value,
        )

        all_actuals.extend(
            y_test.tolist()
        )

        all_baseline_predictions.extend(
            baseline_predictions.tolist()
        )

        fold_metrics = calculate_forecast_metrics(
            y_test,
            baseline_predictions,
        )

        fold_results.append({
            "fold": split["fold"],
            "training_observations": len(
                y_train
            ),
            "validation_observations": len(
                y_test
            ),
            "baseline_value": baseline_value,
            "metrics": fold_metrics,
        })

    baseline_metrics = {
        "baseline_value": float(
            np.mean(
                all_baseline_predictions
            )
        ),
        **calculate_forecast_metrics(
            all_actuals,
            all_baseline_predictions,
        ),
    }

    return (
        all_actuals,
        all_baseline_predictions,
        baseline_metrics,
        fold_results,
    )


# ==========================================================
# AUTOMATIC MODEL SELECTION
# ==========================================================

def select_best_regression_model(
    X,
    y,
    candidate_models=None,
    minimum_observations=14,
):
    """
    Automatically compare regression models using
    walk-forward time-series validation.

    Selection process:

        1. Validate data sufficiency
        2. Validate target variation
        3. Create walk-forward validation periods
        4. Establish historical baseline
        5. Train candidate ML models
        6. Evaluate every model across all folds
        7. Compare ML models against baseline
        8. Select the best baseline-beating model
        9. Fall back to historical mean when ML loses
        10. Retrain selected ML model on all data
    """

    # ------------------------------------------------------
    # LOAD DEFAULT CANDIDATE MODELS
    # ------------------------------------------------------

    if candidate_models is None:
        candidate_models = get_regression_models()

    # ------------------------------------------------------
    # DATA SUFFICIENCY
    # ------------------------------------------------------

    data_assessment = assess_data_sufficiency(
        y,
        minimum_observations=minimum_observations,
    )

    if data_assessment["status"] == "insufficient":

        return {
            "status": "insufficient_data",
            "reason": data_assessment["reason"],
            "data_assessment": data_assessment,
            "best_model_name": None,
            "best_model": None,
            "selected_method": None,
            "baseline_value": None,
            "metrics": None,
            "baseline_metrics": None,
            "model_results": [],
        }

    if data_assessment["status"] == "low_variation":

        return {
            "status": "low_variation",
            "reason": data_assessment["reason"],
            "data_assessment": data_assessment,
            "best_model_name": None,
            "best_model": None,
            "selected_method": None,
            "baseline_value": float(
                y.mean()
            ),
            "metrics": None,
            "baseline_metrics": None,
            "model_results": [],
        }

    # ------------------------------------------------------
    # WALK-FORWARD VALIDATION SPLITS
    # ------------------------------------------------------

    try:

        validation_splits = (
            create_walk_forward_splits(
                X,
                y,
                n_splits=3,
            )
        )

    except ValueError as error:

        return {
            "status": "insufficient_validation_data",
            "reason": str(error),
            "data_assessment": data_assessment,
            "best_model_name": None,
            "best_model": None,
            "selected_method": None,
            "baseline_value": float(
                y.mean()
            ),
            "metrics": None,
            "baseline_metrics": None,
            "model_results": [],
        }

    # ------------------------------------------------------
    # CALCULATE BASELINE ONCE
    # ------------------------------------------------------

    (
        all_actuals,
        all_baseline_predictions,
        baseline_metrics,
        baseline_fold_results,
    ) = calculate_walk_forward_baseline(
        validation_splits
    )

    # ------------------------------------------------------
    # EVALUATE EACH ML MODEL
    # ------------------------------------------------------

    results = []

    for model_name, model in candidate_models.items():

        try:

            all_predictions = []

            fold_results = []

            # --------------------------------------------------
            # WALK THROUGH EACH VALIDATION FOLD
            # --------------------------------------------------

            for split in validation_splits:

                X_train = split["X_train"]
                X_test = split["X_test"]

                y_train = split["y_train"]
                y_test = split["y_test"]

                # ----------------------------------------------
                # TRAIN ONLY ON HISTORICAL DATA
                # ----------------------------------------------

                model.fit(
                    X_train,
                    y_train,
                )

                # ----------------------------------------------
                # PREDICT FUTURE VALIDATION PERIOD
                # ----------------------------------------------

                predictions = model.predict(
                    X_test
                )

                all_predictions.extend(
                    predictions.tolist()
                )

                # ----------------------------------------------
                # FOLD METRICS
                # ----------------------------------------------

                fold_metrics = (
                    calculate_forecast_metrics(
                        y_test,
                        predictions,
                    )
                )

                fold_baseline_metrics = (
                    calculate_forecast_metrics(
                        y_test,
                        np.full(
                            len(y_test),
                            y_train.mean(),
                        ),
                    )
                )

                fold_results.append({
                    "fold": split["fold"],
                    "training_observations": len(
                        y_train
                    ),
                    "validation_observations": len(
                        y_test
                    ),
                    "metrics": fold_metrics,
                    "baseline_metrics": (
                        fold_baseline_metrics
                    ),
                })

            # --------------------------------------------------
            # AGGREGATED MODEL METRICS
            # --------------------------------------------------

            metrics = evaluate_model_against_baseline(
                all_actuals,
                all_predictions,
                baseline_metrics,
            )

            validation_strength = (
                assess_validation_strength(
                    all_actuals,
                    metrics,
                )
            )

            results.append({
                "model_name": model_name,
                "status": "success",
                "metrics": metrics,
                "validation_strength": (
                    validation_strength
                ),
                "fold_results": fold_results,
                "validation_folds": len(
                    validation_splits
                ),
            })

        except Exception as error:

            results.append({
                "model_name": model_name,
                "status": "failed",
                "metrics": None,
                "validation_strength": None,
                "fold_results": [],
                "validation_folds": 0,
                "error": str(error),
            })

    # ------------------------------------------------------
    # FIND SUCCESSFUL MODELS
    # ------------------------------------------------------

    successful_models = [
        result
        for result in results
        if result["status"] == "success"
    ]

    if not successful_models:

        return {
            "status": "no_model_succeeded",
            "reason": (
                "All candidate models failed "
                "during walk-forward validation."
            ),
            "data_assessment": data_assessment,
            "baseline_metrics": baseline_metrics,
            "best_model_name": None,
            "best_model": None,
            "selected_method": "historical_mean",
            "baseline_value": float(
                y.mean()
            ),
            "metrics": None,
            "model_results": results,
            "validation_folds": len(
                validation_splits
            ),
        }

    # ------------------------------------------------------
    # FIND MODELS THAT BEAT THE BASELINE
    # ------------------------------------------------------

    baseline_beating_models = [
        result
        for result in successful_models
        if result["metrics"]["beats_baseline"]
    ]

    # ======================================================
    # BASELINE FALLBACK
    # ======================================================

    if not baseline_beating_models:

        return {
            "status": "baseline_better",
            "reason": (
                "None of the candidate ML models "
                "outperformed the historical-mean "
                "baseline across the walk-forward "
                "validation periods."
            ),
            "data_assessment": data_assessment,
            "baseline_metrics": baseline_metrics,

            # The future forecasting engine should use
            # this method when ML does not outperform
            # the historical baseline.
            "selected_method": "historical_mean",

            # Mean of all available historical observations.
            "baseline_value": float(
                y.mean()
            ),

            "best_model_name": None,
            "best_model": None,
            "metrics": None,
            "model_results": results,
            "validation_folds": len(
                validation_splits
            ),

            # Useful diagnostic information.
            "baseline_fold_results": (
                baseline_fold_results
            ),
        }

    # ======================================================
    # SELECT BEST ML MODEL
    # ======================================================

    best_result = min(
        baseline_beating_models,
        key=lambda result: result[
            "metrics"
        ]["rmse"],
    )

    best_model_name = (
        best_result["model_name"]
    )

    best_model = candidate_models[
        best_model_name
    ]

    # ======================================================
    # DETERMINE FORECAST RELIABILITY
    # ======================================================

    reliability = determine_reliability(
        data_assessment,
        best_result["metrics"],
        best_result["validation_strength"],
    )

    # ======================================================
    # RETRAIN BEST MODEL ON ALL AVAILABLE DATA
    # ======================================================

    best_model.fit(
        X,
        y,
    )

    # ======================================================
    # FINAL SUCCESS RESULT
    # ======================================================

    return {
        "status": "success",
        "reason": None,

        "data_assessment": data_assessment,

        "baseline_metrics": baseline_metrics,

        # Tells the forecast engine that ML should be used.
        "selected_method": "ml_model",

        "baseline_value": float(
            y.mean()
        ),

        "best_model_name": best_model_name,

        "best_model": best_model,

        "metrics": best_result["metrics"],

        "validation_strength": (
            best_result["validation_strength"]
        ),

        "reliability": reliability,

        "model_results": results,

        "validation_folds": len(
            validation_splits
        ),

        "baseline_fold_results": (
            baseline_fold_results
        ),
    }