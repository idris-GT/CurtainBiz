from ml.models.preprocessing import get_preprocessed_regression_models


def get_regression_models():
    """
    Return the regression models available to the ML engine.

    Preprocessing is included inside each model pipeline
    where required.
    """

    return get_preprocessed_regression_models()


def get_model_metadata():
    """
    Metadata used by automatic model selection
    and Advanced Mode.
    """

    return {
        "linear_regression": {
            "name": "Linear Regression",
            "family": "linear",
            "supports_regression": True,
            "requires_scaling": True,
        },

        "ridge": {
            "name": "Ridge Regression",
            "family": "linear",
            "supports_regression": True,
            "requires_scaling": True,
        },

        "lasso": {
            "name": "Lasso Regression",
            "family": "linear",
            "supports_regression": True,
            "requires_scaling": True,
        },

        "random_forest": {
            "name": "Random Forest",
            "family": "tree_ensemble",
            "supports_regression": True,
            "requires_scaling": False,
        },

        "extra_trees": {
            "name": "Extra Trees",
            "family": "tree_ensemble",
            "supports_regression": True,
            "requires_scaling": False,
        },

        "gradient_boosting": {
            "name": "Gradient Boosting",
            "family": "boosting",
            "supports_regression": True,
            "requires_scaling": False,
        },

        "hist_gradient_boosting": {
            "name": "HistGradientBoosting",
            "family": "boosting",
            "supports_regression": True,
            "requires_scaling": False,
        },
    }