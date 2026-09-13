from ml.pipeline import load_and_validate_business_data
from ml.forecasting.forecast_engine import run_forecast_selection


def print_section(title):
    print("\n" + "-" * 70)
    print(f"PROBLEM: {title}")
    print("-" * 70)


def print_forecast_result(problem_name, result):
    print_section(problem_name)

    print(f"Status: {result.get('status')}")

    if result.get("message"):
        print(f"Message: {result['message']}")

    if result.get("reason"):
        print(f"Reason: {result['reason']}")

    if result.get("observations") is not None:
        print(f"Observations used: {result['observations']}")

    # Data sufficiency
    data_assessment = result.get("data_assessment")

    if data_assessment:
        print("\nData assessment:")
        print(f"  Status: {data_assessment.get('status')}")
        print(f"  Observations: {data_assessment.get('observations')}")
        print(f"  Unique values: {data_assessment.get('unique_values')}")
        print(f"  Has variation: {data_assessment.get('has_variation')}")

        if data_assessment.get("reason"):
            print(f"  Reason: {data_assessment['reason']}")

    # Baseline
    baseline = result.get("baseline_metrics")

    if baseline:
        print("\nBaseline:")
        print(f"  Baseline value: {baseline.get('baseline_value'):.4f}")
        print(f"  Baseline MAE: {baseline.get('mae'):.4f}")
        print(f"  Baseline RMSE: {baseline.get('rmse'):.4f}")
        print(f"  Baseline R²: {baseline.get('r2'):.4f}")

    # Selected model
    if result.get("best_model_name"):
        print(f"\nBest model: {result['best_model_name']}")

    metrics = result.get("metrics")

    if metrics:
        print("\nValidation metrics:")
        print(f"  MAE: {metrics.get('mae', 0):.4f}")
        print(f"  RMSE: {metrics.get('rmse', 0):.4f}")
        print(f"  R²: {metrics.get('r2', 0):.4f}")
        print(
            f"  Improvement vs baseline: "
            f"{metrics.get('improvement_vs_baseline_percent', 0):.2f}%"
        )
        print(f"  Beats baseline: {metrics.get('beats_baseline')}")

    # Validation strength
    validation_strength = result.get("validation_strength")

    if validation_strength:
        print("\nValidation strength:")
        print(
            f"  Validation observations: "
            f"{validation_strength.get('validation_observations')}"
        )

        warnings = validation_strength.get("warnings", [])

        if warnings:
            for warning in warnings:
                print(f"  WARNING: {warning}")
        else:
            print("  No validation warnings.")

    # Reliability
    reliability = result.get("reliability")

    if reliability:
        print("\nReliability:")
        print(f"  Level: {reliability.get('level', 'unknown').upper()}")
        print(f"  Reason: {reliability.get('reason')}")

    # Candidate models
    model_results = result.get("model_results", [])

    if model_results:
        print("\nCandidate models:")

        for model_result in model_results:
            model_name = model_result.get("model_name")
            model_metrics = model_result.get("metrics", {})

            if model_result.get("status") == "failed":
                print(
                    f"  {model_name}: FAILED - "
                    f"{model_result.get('error')}"
                )
                continue

            print(
                f"  {model_name}: "
                f"RMSE={model_metrics.get('rmse', 0):.4f}, "
                f"MAE={model_metrics.get('mae', 0):.4f}, "
                f"R²={model_metrics.get('r2', 0):.4f}, "
                f"beats_baseline={model_metrics.get('beats_baseline')}"
            )


def main():
    print("=" * 70)
    print("AUTOMATIC FORECAST MODEL SELECTION")
    print("=" * 70)

    dataframes, quality_report, validation_report = (
        load_and_validate_business_data()
    )

    problems = [
        "revenue_forecast",
        "order_forecast",
        "production_workload_forecast",
        "delivery_workload_forecast",
        "cash_inflow_forecast",
    ]

    for problem_name in problems:
        try:
            result = run_forecast_selection(
                dataframes,
                problem_name,
            )

            print_forecast_result(problem_name, result)

        except Exception as error:
            print_section(problem_name)
            print("Status: ERROR")
            print(f"Error: {error}")

    print("\n" + "=" * 70)
    print("FORECAST MODEL SELECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()