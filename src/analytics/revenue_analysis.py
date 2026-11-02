import pandas as pd


def get_month_data(df: pd.DataFrame, month: str) -> pd.DataFrame:
    return df[df["Month"] == month].copy()


def calculate_month_metrics(df_month: pd.DataFrame) -> dict:
    revenue = df_month["Revenue"].sum()
    orders = df_month["InvoiceNo"].nunique()
    quantity = df_month["Quantity"].sum()
    customers = df_month["CustomerID"].nunique()

    average_order_value = (
        df_month
        .groupby("InvoiceNo")["Revenue"]
        .sum()
        .mean()
    )

    return {
        "revenue": float(revenue),
        "orders": int(orders),
        "quantity": int(quantity),
        "customers": int(customers),
        "average_order_value": float(average_order_value),
    }


def calculate_percentage_change(
    previous_value: float,
    current_value: float
) -> float:
    if previous_value == 0:
        return 0.0

    return (
        (current_value - previous_value)
        / previous_value
        * 100
    )


def compare_dimension(
    previous_df: pd.DataFrame,
    current_df: pd.DataFrame,
    dimension: str,
    top_n: int = 10
) -> pd.DataFrame:
    previous = (
        previous_df
        .groupby(dimension)["Revenue"]
        .sum()
    )

    current = (
        current_df
        .groupby(dimension)["Revenue"]
        .sum()
    )

    comparison = pd.concat(
        [previous, current],
        axis=1,
        keys=[
            "PreviousRevenue",
            "CurrentRevenue",
        ]
    ).fillna(0)

    comparison["RevenueChange"] = (
        comparison["CurrentRevenue"]
        - comparison["PreviousRevenue"]
    )

    comparison = comparison.sort_values(
        "RevenueChange"
    )

    return comparison.head(top_n)


def analyze_revenue_change(
    df: pd.DataFrame,
    previous_month: str,
    current_month: str,
    top_n: int = 10
) -> dict:
    previous_df = get_month_data(
        df,
        previous_month
    )

    current_df = get_month_data(
        df,
        current_month
    )

    if previous_df.empty:
        raise ValueError(
            f"No data found for previous month: {previous_month}"
        )

    if current_df.empty:
        raise ValueError(
            f"No data found for current month: {current_month}"
        )

    previous_metrics = calculate_month_metrics(
        previous_df
    )

    current_metrics = calculate_month_metrics(
        current_df
    )

    changes = {}

    for metric in previous_metrics:
        changes[metric] = calculate_percentage_change(
            previous_metrics[metric],
            current_metrics[metric]
        )

    revenue_drop = (
        previous_metrics["revenue"]
        - current_metrics["revenue"]
    )

    product_declines = compare_dimension(
        previous_df,
        current_df,
        "Description",
        top_n
    )

    country_declines = compare_dimension(
        previous_df,
        current_df,
        "Country",
        top_n
    )

    customer_previous = previous_df.dropna(
        subset=["CustomerID"]
    )

    customer_current = current_df.dropna(
        subset=["CustomerID"]
    )

    customer_declines = compare_dimension(
        customer_previous,
        customer_current,
        "CustomerID",
        top_n
    )

    return {
        "previous_month": previous_month,
        "current_month": current_month,
        "previous_metrics": previous_metrics,
        "current_metrics": current_metrics,
        "percentage_changes": changes,
        "revenue_drop": float(revenue_drop),
        "top_product_declines": product_declines,
        "top_country_declines": country_declines,
        "top_customer_declines": customer_declines,
    }
def dataframe_to_records(df: pd.DataFrame) -> list:
    data = df.reset_index()

    for column in data.columns:
        if pd.api.types.is_numeric_dtype(data[column]):
            data[column] = data[column].round(2)

    return data.to_dict(orient="records")

def build_revenue_analysis_report(
    df: pd.DataFrame,
    previous_month: str,
    current_month: str,
    top_n: int = 5
) -> dict:
    analysis = analyze_revenue_change(
        df=df,
        previous_month=previous_month,
        current_month=current_month,
        top_n=top_n,
    )

    percentage_changes = {
        key: round(value, 2)
        for key, value
        in analysis["percentage_changes"].items()
    }

    return {
        "period": {
            "previous_month": previous_month,
            "current_month": current_month,
        },
        "metrics": {
            "previous": {
                key: round(value, 2)
                for key, value
                in analysis["previous_metrics"].items()
            },
            "current": {
                key: round(value, 2)
                for key, value
                in analysis["current_metrics"].items()
            },
            "percentage_changes": percentage_changes,
        },
        "revenue_drop": round(
            analysis["revenue_drop"],
            2
        ),
        "top_declining_products": dataframe_to_records(
            analysis["top_product_declines"]
        ),
        "top_declining_countries": dataframe_to_records(
            analysis["top_country_declines"]
        ),
        "top_declining_customers": dataframe_to_records(
            analysis["top_customer_declines"]
        ),
    }