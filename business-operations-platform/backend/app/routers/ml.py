from fastapi import APIRouter, Depends, Query

from app.auth import require_permission

from ml.pipeline import load_and_validate_business_data

from ml.forecasting.forecast_engine import generate_forecast

from ml.forecasting.material_demand_forecast import (
    generate_material_demand_forecasts,
)

from ml.forecasting.product_demand_forecast import (
    generate_product_demand_forecasts,
)

from ml.recommendations.inventory_recommendations import (
    generate_inventory_recommendations,
)

from ml.recommendations.production_recommendations import (
    analyze_production_intelligence,
)

from ml.recommendations.delivery_recommendations import (
    analyze_delivery_intelligence,
)

from ml.recommendations.accounts_recommendations import (
    analyze_accounts_intelligence,
)

from ml.recommendations.admin_intelligence import (
    analyze_admin_intelligence,
)

from ml.intelligence_cache import (
    get_cached,
    start_refresh,
    clear_cache,
)


router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning Intelligence"],
)


# ==========================================================
# COMMON DATA LOADER
# ==========================================================

def _load_business_data():
    """
    Load, clean, validate, and feature-engineer the current
    business data through the existing ML pipeline.
    """

    data, quality, validation = (
        load_and_validate_business_data()
    )

    return data, quality, validation


# ==========================================================
# SALES INTELLIGENCE
# ==========================================================

def _compute_sales_intelligence(
    periods: int,
):
    """
    Perform the complete Sales Intelligence calculation.

    This function is intentionally separate from the API
    endpoint so the expensive ML work can run in the
    background without blocking the HTTP request.
    """

    data, quality, validation = (
        _load_business_data()
    )

    revenue_forecast = generate_forecast(
        data,
        "revenue_forecast",
        periods=periods,
    )

    order_forecast = generate_forecast(
        data,
        "order_forecast",
        periods=periods,
    )

    product_demand_forecast = (
        generate_product_demand_forecasts(
            product_demand_df=data.get(
                "product_demand"
            ),
            products_df=data.get(
                "products"
            ),
            periods=periods,
        )
    )

    return {
        "status": "success",
        "department": "sales",

        "revenue_forecast": (
            revenue_forecast
        ),

        "order_forecast": (
            order_forecast
        ),

        "product_demand_forecast": (
            product_demand_forecast
        ),

        "data_quality": quality,

        "validation": validation,

        "message": (
            "Sales intelligence generated from "
            "validated business data."
        ),
    }


@router.get(
    "/sales-intelligence",
)
def get_sales_intelligence(
    periods: int = Query(
        default=8,
        ge=1,
        le=52,
    ),
    current_user=Depends(
        require_permission("orders.view")
    ),
):
    """
    Return Sales forecasting intelligence.

    The expensive ML calculation runs in the background.
    The first request returns immediately with status=processing.
    Later requests return the cached completed intelligence.
    """

    cached = get_cached(
        "sales_intelligence",
        periods,
    )

    # ------------------------------------------------------
    # CACHE EXISTS AND IS READY
    # ------------------------------------------------------

    if (
        cached is not None
        and cached.get("status") == "success"
        and cached.get("data") is not None
    ):
        response = dict(
            cached["data"]
        )

        response["cache"] = {
            "status": "ready",
            "refreshing": False,
            "updated_at": cached.get(
                "updated_at"
            ),
        }

        return response

    # ------------------------------------------------------
    # CALCULATION ALREADY RUNNING
    # ------------------------------------------------------

    if (
        cached is not None
        and cached.get("refreshing") is True
    ):
        return {
            "status": "processing",
            "department": "sales",
            "cache": {
                "status": "processing",
                "refreshing": True,
                "started_at": cached.get(
                    "started_at"
                ),
                "updated_at": cached.get(
                    "updated_at"
                ),
            },
            "data": cached.get(
                "data"
            ),
            "message": (
                "Sales Intelligence is being "
                "calculated in the background."
            ),
        }

    # ------------------------------------------------------
    # NO CACHE
    #
    # Start the calculation in the background.
    # ------------------------------------------------------

    state = start_refresh(
        name="sales_intelligence",
        periods=periods,
        compute_fn=lambda: (
            _compute_sales_intelligence(
                periods
            )
        ),
    )

    return {
        "status": "processing",
        "department": "sales",
        "cache": {
            "status": "processing",
            "refreshing": True,
            "started_at": state.get(
                "started_at"
            ),
            "updated_at": state.get(
                "updated_at"
            ),
        },
        "data": state.get(
            "data"
        ),
        "message": (
            "Sales Intelligence calculation "
            "started in the background."
        ),
    }


# ==========================================================
# INVENTORY INTELLIGENCE
# ==========================================================

@router.get(
    "/inventory-intelligence",
)
def get_inventory_intelligence(
    periods: int = Query(
        default=8,
        ge=1,
        le=52,
    ),
    current_user=Depends(
        require_permission("inventory.view")
    ),
):
    """
    Return Inventory and material-demand intelligence.

    Includes:
        - Material demand forecasts
        - Current inventory risk
        - Forecasted stock risk
        - Untracked materials
        - Purchase recommendations
    """

    data, quality, validation = (
        _load_business_data()
    )

    material_demand_forecast = (
        generate_material_demand_forecasts(
            data["material_demand"],
            periods=periods,
        )
    )

    inventory_result = (
        generate_inventory_recommendations(
            inventory_df=data.get(
                "inventory"
            ),
            material_demand_forecast=(
                material_demand_forecast
            ),
            materials_df=data.get(
                "materials"
            ),
        )
    )

    return {
        "status": "success",
        "department": "inventory",

        "material_demand_forecast": (
            material_demand_forecast
        ),

        "inventory_intelligence": (
            inventory_result
        ),

        "data_quality": quality,

        "validation": validation,

        "message": (
            "Inventory intelligence generated from "
            "validated inventory and material-demand data."
        ),
    }


# ==========================================================
# PRODUCTION INTELLIGENCE
# ==========================================================

@router.get(
    "/production-intelligence",
)
def get_production_intelligence(
    periods: int = Query(
        default=8,
        ge=1,
        le=52,
    ),
    current_user=Depends(
        require_permission("production.view")
    ),
):
    """
    Return Production workload and capacity intelligence.
    """

    data, quality, validation = (
        _load_business_data()
    )

    forecast = generate_forecast(
        data,
        "production_workload_forecast",
        periods=periods,
    )

    intelligence = (
        analyze_production_intelligence(
            data=data,
            forecast_result=forecast,
        )
    )

    return {
        "status": "success",
        "department": "production",

        "forecast": forecast,

        "intelligence": intelligence,

        "data_quality": quality,

        "validation": validation,

        "message": (
            "Production intelligence generated from "
            "validated production history and workload forecast."
        ),
    }


# ==========================================================
# DELIVERY INTELLIGENCE
# ==========================================================

@router.get(
    "/delivery-intelligence",
)
def get_delivery_intelligence(
    periods: int = Query(
        default=8,
        ge=1,
        le=52,
    ),
    current_user=Depends(
        require_permission("deliveries.view")
    ),
):
    """
    Return Delivery workload and capacity intelligence.
    """

    data, quality, validation = (
        _load_business_data()
    )

    forecast = generate_forecast(
        data,
        "delivery_workload_forecast",
        periods=periods,
    )

    intelligence = (
        analyze_delivery_intelligence(
            data=data,
            forecast_result=forecast,
        )
    )

    return {
        "status": "success",
        "department": "delivery",

        "forecast": forecast,

        "intelligence": intelligence,

        "data_quality": quality,

        "validation": validation,

        "message": (
            "Delivery intelligence generated from "
            "validated delivery history and workload forecast."
        ),
    }


# ==========================================================
# ACCOUNTS INTELLIGENCE
# ==========================================================

@router.get(
    "/accounts-intelligence",
)
def get_accounts_intelligence(
    periods: int = Query(
        default=8,
        ge=1,
        le=52,
    ),
    current_user=Depends(
        require_permission("payments.view")
    ),
):
    """
    Return Accounts and cashflow intelligence.

    Includes:
        - Cash inflow forecast
        - Historical cashflow trend
        - Cashflow risk
        - Forecast reliability
    """

    data, quality, validation = (
        _load_business_data()
    )

    forecast = generate_forecast(
        data,
        "cash_inflow_forecast",
        periods=periods,
    )

    intelligence = (
        analyze_accounts_intelligence(
            data=data,
            forecast_result=forecast,
        )
    )

    return {
        "status": "success",
        "department": "accounts",

        "forecast": forecast,

        "intelligence": intelligence,

        "data_quality": quality,

        "validation": validation,

        "message": (
            "Accounts intelligence generated from "
            "validated payment history and cashflow forecast."
        ),
    }


# ==========================================================
# ADMIN INTELLIGENCE
# ==========================================================

def _compute_admin_intelligence(
    periods: int,
):
    """
    Perform the complete executive intelligence calculation.

    This function is intentionally separate from the API
    endpoint so it can run in the background.
    """

    data, quality, validation = (
        _load_business_data()
    )

    # ------------------------------------------------------
    # SALES
    # ------------------------------------------------------

    revenue_forecast = generate_forecast(
        data,
        "revenue_forecast",
        periods=periods,
    )

    order_forecast = generate_forecast(
        data,
        "order_forecast",
        periods=periods,
    )

    product_demand_forecast = (
        generate_product_demand_forecasts(
            product_demand_df=data.get(
                "product_demand"
            ),
            products_df=data.get(
                "products"
            ),
            periods=periods,
        )
    )

    # ------------------------------------------------------
    # INVENTORY
    # ------------------------------------------------------

    material_demand_forecast = (
        generate_material_demand_forecasts(
            data["material_demand"],
            periods=periods,
        )
    )

    inventory_result = (
        generate_inventory_recommendations(
            inventory_df=data.get(
                "inventory"
            ),
            material_demand_forecast=(
                material_demand_forecast
            ),
            materials_df=data.get(
                "materials"
            ),
        )
    )

    # ------------------------------------------------------
    # PRODUCTION
    # ------------------------------------------------------

    production_forecast = generate_forecast(
        data,
        "production_workload_forecast",
        periods=periods,
    )

    production_result = (
        analyze_production_intelligence(
            data=data,
            forecast_result=production_forecast,
        )
    )

    # ------------------------------------------------------
    # DELIVERY
    # ------------------------------------------------------

    delivery_forecast = generate_forecast(
        data,
        "delivery_workload_forecast",
        periods=periods,
    )

    delivery_result = (
        analyze_delivery_intelligence(
            data=data,
            forecast_result=delivery_forecast,
        )
    )

    # ------------------------------------------------------
    # ACCOUNTS
    # ------------------------------------------------------

    cashflow_forecast = generate_forecast(
        data,
        "cash_inflow_forecast",
        periods=periods,
    )

    accounts_result = (
        analyze_accounts_intelligence(
            data=data,
            forecast_result=cashflow_forecast,
        )
    )

    # ------------------------------------------------------
    # ADMIN AGGREGATION
    # ------------------------------------------------------

    admin_result = analyze_admin_intelligence(
        sales_revenue_forecast=(
            revenue_forecast
        ),
        sales_order_forecast=(
            order_forecast
        ),
        inventory_result=(
            inventory_result
        ),
        production_result=(
            production_result
        ),
        delivery_result=(
            delivery_result
        ),
        accounts_result=(
            accounts_result
        ),
    )

    return {
        "status": "success",
        "department": "admin",

        "intelligence": admin_result,

        "forecasts": {
            "revenue": revenue_forecast,

            "orders": order_forecast,

            "product_demand": (
                product_demand_forecast
            ),

            "material_demand": (
                material_demand_forecast
            ),

            "production": production_forecast,

            "delivery": delivery_forecast,

            "cashflow": cashflow_forecast,
        },

        "department_intelligence": {
            "inventory": inventory_result,

            "production": production_result,

            "delivery": delivery_result,

            "accounts": accounts_result,
        },

        "data_quality": quality,

        "validation": validation,

        "message": (
            "Admin Intelligence generated by combining "
            "validated forecasts and department-level "
            "operational intelligence."
        ),
    }


@router.get(
    "/admin-intelligence",
)
def get_admin_intelligence(
    periods: int = Query(
        default=8,
        ge=1,
        le=52,
    ),
    current_user=Depends(
        require_permission("reports.view")
    ),
):
    """
    Return executive-level business intelligence.

    The expensive calculation is performed in the background.

    First request:
        Returns immediately with status=processing.

    Later requests:
        Return the cached completed intelligence immediately.

    Existing cached data is preserved while a refresh is running.
    """

    cached = get_cached(
        "admin_intelligence",
        periods,
    )

    # ------------------------------------------------------
    # CACHE EXISTS AND IS READY
    # ------------------------------------------------------

    if (
        cached is not None
        and cached.get("status") == "success"
        and cached.get("data") is not None
    ):
        response = dict(
            cached["data"]
        )

        response["cache"] = {
            "status": "ready",
            "refreshing": False,
            "updated_at": cached.get(
                "updated_at"
            ),
        }

        return response

    # ------------------------------------------------------
    # CALCULATION ALREADY RUNNING
    # ------------------------------------------------------

    if (
        cached is not None
        and cached.get("refreshing") is True
    ):
        response = {
            "status": "processing",
            "department": "admin",

            "cache": {
                "status": "processing",
                "refreshing": True,
                "started_at": cached.get(
                    "started_at"
                ),
                "updated_at": cached.get(
                    "updated_at"
                ),
            },

            "data": cached.get(
                "data"
            ),

            "message": (
                "Business Intelligence is being "
                "calculated in the background."
            ),
        }

        return response

    # ------------------------------------------------------
    # NO CACHE
    #
    # Start the calculation in the background.
    # ------------------------------------------------------

    state = start_refresh(
        name="admin_intelligence",
        periods=periods,
        compute_fn=lambda: (
            _compute_admin_intelligence(
                periods
            )
        ),
    )

    return {
        "status": "processing",
        "department": "admin",

        "cache": {
            "status": "processing",
            "refreshing": True,
            "started_at": state.get(
                "started_at"
            ),
            "updated_at": state.get(
                "updated_at"
            ),
        },

        "data": state.get(
            "data"
        ),

        "message": (
            "Business Intelligence calculation "
            "started in the background."
        ),
    }


# ==========================================================
# ADMIN INTELLIGENCE — MANUAL REFRESH
# ==========================================================

@router.post(
    "/admin-intelligence/refresh",
)
def refresh_admin_intelligence(
    periods: int = Query(
        default=8,
        ge=1,
        le=52,
    ),
    current_user=Depends(
        require_permission("reports.view")
    ),
):
    """
    Start a background refresh of Admin Intelligence.

    The API returns immediately.
    """

    state = start_refresh(
        name="admin_intelligence",
        periods=periods,
        compute_fn=lambda: (
            _compute_admin_intelligence(
                periods
            )
        ),
    )

    return {
        "status": (
            "processing"
            if state.get("refreshing")
            else state.get(
                "status",
                "processing",
            )
        ),

        "department": "admin",

        "refreshing": state.get(
            "refreshing",
            False,
        ),

        "started_at": state.get(
            "started_at"
        ),

        "updated_at": state.get(
            "updated_at"
        ),

        "message": (
            "Admin Intelligence refresh "
            "started in the background."
        ),
    }


# ==========================================================
# ADMIN INTELLIGENCE — CLEAR CACHE
# ==========================================================

@router.delete(
    "/admin-intelligence/cache",
)
def clear_admin_intelligence_cache(
    current_user=Depends(
        require_permission("reports.view")
    ),
):
    """
    Clear cached Admin Intelligence.

    The next GET request will trigger a new
    background calculation.
    """

    clear_cache(
        "admin_intelligence"
    )

    return {
        "status": "success",
        "message": (
            "Admin Intelligence cache cleared."
        ),
    }