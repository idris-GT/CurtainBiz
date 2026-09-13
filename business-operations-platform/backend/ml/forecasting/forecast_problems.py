FORECAST_PROBLEMS = {
    "revenue_forecast": {
        "name": "Revenue Forecast",
        "description": "Forecast future business revenue.",
        "feature_set": "sales",
        "date_column": "date",
        "target_column": "revenue",
        "frequency": "weekly",
        "business_area": "sales",
        "minimum_observations": 12,
    },

    "order_forecast": {
        "name": "Order Forecast",
        "description": "Forecast the number of future orders.",
        "feature_set": "orders",
        "date_column": "date",
        "target_column": "order_count",
        "frequency": "weekly",
        "business_area": "sales",
        "minimum_observations": 12,
    },

    "product_demand_forecast": {
        "name": "Product Demand Forecast",
        "description": "Forecast future demand for individual products.",
        "feature_set": "product_demand",
        "date_column": "date",
        "target_column": "quantity",
        "group_column": "product_id",
        "frequency": "daily",
        "business_area": "sales",
        "minimum_observations": 10,
    },

    "production_workload_forecast": {
        "name": "Production Workload Forecast",
        "description": "Forecast future production workload.",
        "feature_set": "production",
        "date_column": "date",
        "target_column": "production_count",
        "frequency": "weekly",
        "business_area": "production",
        "minimum_observations": 12,
    },

    "delivery_workload_forecast": {
        "name": "Delivery Workload Forecast",
        "description": "Forecast future delivery workload.",
        "feature_set": "deliveries",
        "date_column": "date",
        "target_column": "delivery_count",
        "frequency": "weekly",
        "business_area": "delivery",
        "minimum_observations": 12,
    },

    "cash_inflow_forecast": {
        "name": "Cash Inflow Forecast",
        "description": "Forecast future payment cash inflow.",
        "feature_set": "payments",
        "date_column": "date",
        "target_column": "cash_inflow",
        "frequency": "weekly",
        "business_area": "accounts",
        "minimum_observations": 12,
    },
}


def get_forecast_problem(problem_name):
    """
    Return the definition of a supported forecasting problem.
    """

    if problem_name not in FORECAST_PROBLEMS:
        raise ValueError(
            f"Unknown forecast problem: {problem_name}"
        )

    return FORECAST_PROBLEMS[problem_name]


def list_forecast_problems():
    """
    Return all supported forecasting problems.
    """

    return FORECAST_PROBLEMS.copy()