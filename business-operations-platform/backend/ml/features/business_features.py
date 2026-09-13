import pandas as pd


def _ensure_datetime(df, column):
    """Safely convert a column to datetime."""
    result = df.copy()

    if column in result.columns:
        result[column] = pd.to_datetime(
            result[column],
            errors="coerce",
            utc=True
        )

    return result


# ==========================================================
# SALES / REVENUE FEATURES
# ==========================================================

def build_sales_features(dataframes):
    """
    Build daily sales and revenue features from orders.

    Output:
        date
        order_count
        revenue
        average_order_value
    """

    orders = dataframes["orders"].copy()

    orders = _ensure_datetime(orders, "order_date")

    orders = orders.dropna(subset=["order_date"])

    orders["date"] = orders["order_date"].dt.floor("D")

    daily = (
        orders.groupby("date")
        .agg(
            order_count=("id", "nunique"),
            revenue=("total_amount", "sum"),
        )
        .reset_index()
    )

    daily["average_order_value"] = (
        daily["revenue"] / daily["order_count"]
    )

    return daily.sort_values("date").reset_index(drop=True)


# ==========================================================
# ORDER FEATURES
# ==========================================================

def build_order_features(dataframes):
    """
    Build daily order features.

    Includes order counts by status where possible.
    """

    orders = dataframes["orders"].copy()

    orders = _ensure_datetime(orders, "order_date")

    orders = orders.dropna(subset=["order_date"])

    orders["date"] = orders["order_date"].dt.floor("D")

    daily = (
        orders.groupby("date")
        .agg(
            order_count=("id", "nunique"),
        )
        .reset_index()
    )

    if "status" in orders.columns:
        status_counts = pd.crosstab(
            orders["date"],
            orders["status"]
        ).reset_index()

        status_counts.columns = [
            "date"
            if column == "date"
            else f"orders_{str(column).lower()}"
            for column in status_counts.columns
        ]

        daily = daily.merge(
            status_counts,
            on="date",
            how="left"
        )

    return daily.sort_values("date").reset_index(drop=True)


# ==========================================================
# PRODUCT DEMAND FEATURES
# ==========================================================

def build_product_demand_features(dataframes):
    """
    Build product-level demand features from order items.

    Output:
        date
        product_id
        quantity
        revenue
    """

    order_items = dataframes["order_items"].copy()
    orders = dataframes["orders"].copy()

    orders = _ensure_datetime(orders, "order_date")

    required_order_columns = ["id", "order_date"]

    if not all(
        column in orders.columns
        for column in required_order_columns
    ):
        return pd.DataFrame()

    order_items = order_items.merge(
        orders[["id", "order_date"]],
        left_on="order_id",
        right_on="id",
        how="inner",
        suffixes=("", "_order")
    )

    order_items["date"] = (
        order_items["order_date"]
        .dt.floor("D")
    )

    demand = (
        order_items.groupby(
            ["date", "product_id"]
        )
        .agg(
            quantity=("quantity", "sum"),
            revenue=("total_price", "sum"),
        )
        .reset_index()
    )

    return demand.sort_values(
        ["date", "product_id"]
    ).reset_index(drop=True)


# ==========================================================
# INVENTORY FEATURES
# ==========================================================

def build_inventory_features(dataframes):
    """
    Build current inventory intelligence features.

    Historical inventory movement requires stock_transactions.
    """

    inventory = dataframes["inventory"].copy()
    materials = dataframes["materials"].copy()

    if inventory.empty:
        return pd.DataFrame()

    features = inventory.copy()

    if "material_id" in features.columns and "id" in materials.columns:

        material_columns = [
            column
            for column in [
                "id",
                "name",
                "category",
                "unit",
                "minimum_stock",
                "cost_per_unit",
            ]
            if column in materials.columns
        ]

        features = features.merge(
            materials[material_columns],
            left_on="material_id",
            right_on="id",
            how="left",
            suffixes=("", "_material")
        )

    features["available_after_reservation"] = (
        features["quantity_available"]
        - features["reserved_quantity"]
    )

    if "minimum_stock" in features.columns:

        features["below_minimum_stock"] = (
            features["available_after_reservation"]
            < features["minimum_stock"]
        )

        features["stock_deficit"] = (
            features["minimum_stock"]
            - features["available_after_reservation"]
        ).clip(lower=0)

    return features


# ==========================================================
# MATERIAL DEMAND FEATURES
# ==========================================================

def build_material_demand_features(dataframes):
    """
    Build material demand from historical stock transactions.

    If stock_transactions has no historical records,
    return an empty DataFrame rather than inventing demand.
    """

    transactions = dataframes["stock_transactions"].copy()

    if transactions.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "material_id",
                "inbound_quantity",
                "outbound_quantity",
            ]
        )

    transactions = _ensure_datetime(
        transactions,
        "created_at"
    )

    transactions = transactions.dropna(
        subset=["created_at"]
    )

    transactions["date"] = (
        transactions["created_at"].dt.floor("D")
    )

    transactions["quantity"] = pd.to_numeric(
        transactions["quantity"],
        errors="coerce"
    ).fillna(0)

    transactions["transaction_type"] = (
        transactions["transaction_type"]
        .astype(str)
        .str.upper()
    )

    transactions["inbound_quantity"] = transactions[
        "quantity"
    ].where(
        transactions["transaction_type"].isin(
            ["IN", "PURCHASE", "RECEIPT", "STOCK_IN"]
        ),
        0
    )

    transactions["outbound_quantity"] = transactions[
        "quantity"
    ].where(
        transactions["transaction_type"].isin(
            ["OUT", "SALE", "USAGE", "CONSUMPTION", "STOCK_OUT", "ISSUE"]
        ),
        0
    )

    demand = (
        transactions.groupby(
            ["date", "material_id"]
        )
        .agg(
            inbound_quantity=("inbound_quantity", "sum"),
            outbound_quantity=("outbound_quantity", "sum"),
        )
        .reset_index()
    )

    return demand.sort_values(
        ["date", "material_id"]
    ).reset_index(drop=True)


# ==========================================================
# PRODUCTION WORKLOAD FEATURES
# ==========================================================

def build_production_features(dataframes):
    """
    Build daily production workload features.
    """

    production = dataframes["production"].copy()

    if production.empty:
        return pd.DataFrame()

    production = _ensure_datetime(
        production,
        "start_date"
    )

    production = production.dropna(
        subset=["start_date"]
    )

    production["date"] = (
        production["start_date"].dt.floor("D")
    )

    daily = (
        production.groupby("date")
        .agg(
            production_count=("id", "nunique"),
        )
        .reset_index()
    )

    if "status" in production.columns:

        status_counts = pd.crosstab(
            production["date"],
            production["status"]
        ).reset_index()

        status_counts.columns = [
            "date"
            if column == "date"
            else f"production_{str(column).lower()}"
            for column in status_counts.columns
        ]

        daily = daily.merge(
            status_counts,
            on="date",
            how="left"
        )

    return daily.sort_values("date").reset_index(drop=True)


# ==========================================================
# DELIVERY WORKLOAD FEATURES
# ==========================================================

def build_delivery_features(dataframes):
    """
    Build daily delivery workload features.
    """

    deliveries = dataframes["deliveries"].copy()

    if deliveries.empty:
        return pd.DataFrame()

    deliveries = _ensure_datetime(
        deliveries,
        "scheduled_date"
    )

    deliveries = deliveries.dropna(
        subset=["scheduled_date"]
    )

    deliveries["date"] = (
        deliveries["scheduled_date"].dt.floor("D")
    )

    daily = (
        deliveries.groupby("date")
        .agg(
            delivery_count=("id", "nunique"),
        )
        .reset_index()
    )

    if "status" in deliveries.columns:

        status_counts = pd.crosstab(
            deliveries["date"],
            deliveries["status"]
        ).reset_index()

        status_counts.columns = [
            "date"
            if column == "date"
            else f"deliveries_{str(column).lower()}"
            for column in status_counts.columns
        ]

        daily = daily.merge(
            status_counts,
            on="date",
            how="left"
        )

    return daily.sort_values("date").reset_index(drop=True)


# ==========================================================
# PAYMENT / CASHFLOW FEATURES
# ==========================================================

def build_payment_features(dataframes):
    """
    Build daily payment and cash-inflow features.
    """

    payments = dataframes["payments"].copy()

    if payments.empty:
        return pd.DataFrame()

    payments = _ensure_datetime(
        payments,
        "payment_date"
    )

    payments = payments.dropna(
        subset=["payment_date"]
    )

    payments["amount"] = pd.to_numeric(
        payments["amount"],
        errors="coerce"
    ).fillna(0)

    payments["date"] = (
        payments["payment_date"].dt.floor("D")
    )

    daily = (
        payments.groupby("date")
        .agg(
            payment_count=("id", "nunique"),
            cash_inflow=("amount", "sum"),
        )
        .reset_index()
    )

    daily["average_payment"] = (
        daily["cash_inflow"]
        / daily["payment_count"]
    )

    return daily.sort_values("date").reset_index(drop=True)


# ==========================================================
# COMPLETE FEATURE ENGINE
# ==========================================================

def build_business_features(dataframes):
    """
    Build all currently available business features.

    Returns a dictionary of feature DataFrames.
    """

    return {
        "sales": build_sales_features(dataframes),
        "orders": build_order_features(dataframes),
        "product_demand": build_product_demand_features(dataframes),
        "inventory": build_inventory_features(dataframes),
        "material_demand": build_material_demand_features(dataframes),
        "production": build_production_features(dataframes),
        "deliveries": build_delivery_features(dataframes),
        "payments": build_payment_features(dataframes),
    }