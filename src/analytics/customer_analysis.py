import pandas as pd


def get_month_data(
    df: pd.DataFrame,
    month: str,
) -> pd.DataFrame:
    return df[
        df["Month"] == month
    ].copy()


def calculate_customer_revenue(
    df: pd.DataFrame,
) -> pd.DataFrame:
    customer_revenue = (
        df.dropna(
            subset=["CustomerID"]
        )
        .groupby(
            "CustomerID",
            as_index=False,
        )
        .agg(
            revenue=(
                "Revenue",
                "sum",
            ),
            orders=(
                "InvoiceNo",
                "nunique",
            ),
            quantity=(
                "Quantity",
                "sum",
            ),
        )
    )

    return customer_revenue


def compare_customer_revenue(
    df: pd.DataFrame,
    previous_month: str,
    current_month: str,
) -> pd.DataFrame:
    previous_data = get_month_data(
        df,
        previous_month,
    )

    current_data = get_month_data(
        df,
        current_month,
    )

    previous_customers = (
        calculate_customer_revenue(
            previous_data
        )
        .rename(
            columns={
                "revenue": "previous_revenue",
                "orders": "previous_orders",
                "quantity": "previous_quantity",
            }
        )
    )

    current_customers = (
        calculate_customer_revenue(
            current_data
        )
        .rename(
            columns={
                "revenue": "current_revenue",
                "orders": "current_orders",
                "quantity": "current_quantity",
            }
        )
    )

    comparison = previous_customers.merge(
        current_customers,
        on="CustomerID",
        how="outer",
    )

    numeric_columns = [
        "previous_revenue",
        "current_revenue",
        "previous_orders",
        "current_orders",
        "previous_quantity",
        "current_quantity",
    ]

    comparison[
        numeric_columns
    ] = comparison[
        numeric_columns
    ].fillna(0)

    comparison["revenue_change"] = (
        comparison["current_revenue"]
        - comparison["previous_revenue"]
    )

    comparison["order_change"] = (
        comparison["current_orders"]
        - comparison["previous_orders"]
    )

    comparison["quantity_change"] = (
        comparison["current_quantity"]
        - comparison["previous_quantity"]
    )

    return comparison


def calculate_total_revenue_change(
    df: pd.DataFrame,
    previous_month: str,
    current_month: str,
) -> float:
    previous_revenue = get_month_data(
        df,
        previous_month,
    )["Revenue"].sum()

    current_revenue = get_month_data(
        df,
        current_month,
    )["Revenue"].sum()

    return float(
        current_revenue
        - previous_revenue
    )


def dataframe_to_records(
    dataframe: pd.DataFrame,
) -> list[dict]:
    records = []

    for row in dataframe.to_dict(
        orient="records"
    ):
        clean_row = {}

        for key, value in row.items():
            if pd.isna(value):
                clean_row[key] = None
            elif isinstance(
                value,
                float,
            ):
                clean_row[key] = round(
                    float(value),
                    2,
                )
            elif hasattr(
                value,
                "item",
            ):
                clean_row[key] = (
                    value.item()
                )
            else:
                clean_row[key] = value

        records.append(
            clean_row
        )

    return records


def build_customer_contribution_report(
    df: pd.DataFrame,
    previous_month: str,
    current_month: str,
    top_n: int = 10,
) -> dict:
    comparison = compare_customer_revenue(
        df=df,
        previous_month=previous_month,
        current_month=current_month,
    )

    biggest_declines = (
        comparison
        .sort_values(
            "revenue_change",
            ascending=True,
        )
        .head(top_n)
        .copy()
    )

    biggest_growth = (
        comparison
        .sort_values(
            "revenue_change",
            ascending=False,
        )
        .head(top_n)
        .copy()
    )

    total_revenue_change = (
        calculate_total_revenue_change(
            df=df,
            previous_month=previous_month,
            current_month=current_month,
        )
    )

    gross_decline = float(
        biggest_declines[
            "revenue_change"
        ].sum()
    )

    return {
        "period": {
            "previous_month": (
                previous_month
            ),
            "current_month": (
                current_month
            ),
        },
        "total_revenue_change": round(
            total_revenue_change,
            2,
        ),
        "top_customer_declines": (
            dataframe_to_records(
                biggest_declines
            )
        ),
        "top_customer_growth": (
            dataframe_to_records(
                biggest_growth
            )
        ),
        "top_declines_combined_change": round(
            gross_decline,
            2,
        ),
    }