import pandas as pd


def filter_by_month(
    df: pd.DataFrame,
    month: str | None = None
) -> pd.DataFrame:
    if month is None:
        return df.copy()

    filtered_df = df[
        df["Month"] == month
    ].copy()

    if filtered_df.empty:
        raise ValueError(
            f"No data found for month: {month}"
        )

    return filtered_df


def calculate_business_kpis(
    df: pd.DataFrame
) -> dict:
    revenue = df["Revenue"].sum()
    orders = df["InvoiceNo"].nunique()
    quantity = df["Quantity"].sum()
    customers = df["CustomerID"].nunique()
    products = df["StockCode"].nunique()

    order_revenue = (
        df
        .groupby("InvoiceNo")["Revenue"]
        .sum()
    )

    average_order_value = order_revenue.mean()

    revenue_per_customer = (
        revenue / customers
        if customers > 0
        else 0
    )

    return {
        "revenue": round(float(revenue), 2),
        "orders": int(orders),
        "quantity": int(quantity),
        "customers": int(customers),
        "products": int(products),
        "average_order_value": round(
            float(average_order_value),
            2
        ),
        "revenue_per_customer": round(
            float(revenue_per_customer),
            2
        ),
    }


def get_top_products(
    df: pd.DataFrame,
    top_n: int = 5
) -> list:
    products = (
        df
        .groupby("Description")
        .agg(
            Revenue=("Revenue", "sum"),
            Quantity=("Quantity", "sum"),
        )
        .sort_values(
            "Revenue",
            ascending=False
        )
        .head(top_n)
        .reset_index()
    )

    products["Revenue"] = (
        products["Revenue"].round(2)
    )

    return products.to_dict(
        orient="records"
    )


def get_top_countries(
    df: pd.DataFrame,
    top_n: int = 5
) -> list:
    countries = (
        df
        .groupby("Country")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Customers=("CustomerID", "nunique"),
        )
        .sort_values(
            "Revenue",
            ascending=False
        )
        .head(top_n)
        .reset_index()
    )

    countries["Revenue"] = (
        countries["Revenue"].round(2)
    )

    return countries.to_dict(
        orient="records"
    )


def get_top_customers(
    df: pd.DataFrame,
    top_n: int = 5
) -> list:
    customer_df = df.dropna(
        subset=["CustomerID"]
    )

    customers = (
        customer_df
        .groupby("CustomerID")
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("InvoiceNo", "nunique"),
            Quantity=("Quantity", "sum"),
        )
        .sort_values(
            "Revenue",
            ascending=False
        )
        .head(top_n)
        .reset_index()
    )

    customers["CustomerID"] = (
        customers["CustomerID"]
        .astype(int)
        .astype(str)
    )

    customers["Revenue"] = (
        customers["Revenue"].round(2)
    )

    return customers.to_dict(
        orient="records"
    )


def build_business_performance_report(
    df: pd.DataFrame,
    month: str | None = None,
    top_n: int = 5
) -> dict:
    analysis_df = filter_by_month(
        df,
        month
    )

    period = (
        month
        if month is not None
        else "full_dataset"
    )

    return {
        "period": period,
        "kpis": calculate_business_kpis(
            analysis_df
        ),
        "top_products": get_top_products(
            analysis_df,
            top_n
        ),
        "top_countries": get_top_countries(
            analysis_df,
            top_n
        ),
        "top_customers": get_top_customers(
            analysis_df,
            top_n
        ),
    }
    