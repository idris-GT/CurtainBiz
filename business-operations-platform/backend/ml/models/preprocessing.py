from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import (
    LinearRegression,
    Ridge,
    Lasso,
)
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    GradientBoostingRegressor,
    HistGradientBoostingRegressor,
)


def get_preprocessed_regression_models():
    """
    Return the regression model registry with appropriate
    preprocessing.

    Linear models use StandardScaler because their
    coefficients are sensitive to feature scale.

    Tree-based models do not require scaling.

    Lasso uses stronger regularisation and a high iteration
    limit to improve convergence on business time-series
    feature sets.
    """

    return {

        # ==================================================
        # LINEAR MODELS
        # ==================================================

        "linear_regression": Pipeline([
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                LinearRegression(),
            ),
        ]),

        "ridge": Pipeline([
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                Ridge(
                    alpha=1.0,
                ),
            ),
        ]),

        "lasso": Pipeline([
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "model",
                Lasso(
                    alpha=10.0,
                    max_iter=500000,
                    tol=1e-3,
                    selection="cyclic",
                ),
            ),
        ]),

        # ==================================================
        # TREE ENSEMBLES
        # ==================================================

        "random_forest": RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
        ),

        "extra_trees": ExtraTreesRegressor(
            n_estimators=200,
            random_state=42,
            n_jobs=-1,
        ),

        # ==================================================
        # BOOSTING
        # ==================================================

        "gradient_boosting": GradientBoostingRegressor(
            random_state=42,
        ),

        "hist_gradient_boosting": (
            HistGradientBoostingRegressor(
                random_state=42,
            )
        ),
    }