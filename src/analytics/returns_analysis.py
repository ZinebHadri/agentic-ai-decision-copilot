import pandas as pd


def prepare_returns_data(
    df_raw: pd.DataFrame
) -> pd.DataFrame:
    returns_df = df_raw[
        (
            df_raw["InvoiceNo"]
            .astype(str)
            .str.startswith("C")
        )
        | (df_raw["Quantity"] < 0)
    ].copy()

    returns_df["ReturnQuantity"] = (
        returns_df["Quantity"].abs()
    )

    returns_df["ReturnValue"] = (
        returns_df["ReturnQuantity"]
        * returns_df["UnitPrice"].abs()
    )

    returns_df["Month"] = (
        returns_df["InvoiceDate"]
        .dt.to_period("M")
        .astype(str)
    )

    return returns_df


def calculate_return_kpis(
    returns_df: pd.DataFrame
) -> dict:
    return {
        "return_transactions": int(
            returns_df["InvoiceNo"].nunique()
        ),
        "returned_units": int(
            returns_df["ReturnQuantity"].sum()
        ),
        "return_value": round(
            float(
                returns_df["ReturnValue"].sum()
            ),
            2
        ),
        "customers_with_returns": int(
            returns_df["CustomerID"].nunique()
        ),
    }


def get_top_returned_products(
    returns_df: pd.DataFrame,
    top_n: int = 5
) -> list:
    products = (
        returns_df
        .dropna(subset=["Description"])
        .groupby("Description")
        .agg(
            ReturnedUnits=(
                "ReturnQuantity",
                "sum"
            ),
            ReturnValue=(
                "ReturnValue",
                "sum"
            ),
            ReturnTransactions=(
                "InvoiceNo",
                "nunique"
            ),
        )
        .sort_values(
            "ReturnValue",
            ascending=False
        )
        .head(top_n)
        .reset_index()
    )

    products["ReturnValue"] = (
        products["ReturnValue"].round(2)
    )

    return products.to_dict(
        orient="records"
    )


def get_top_return_countries(
    returns_df: pd.DataFrame,
    top_n: int = 5
) -> list:
    countries = (
        returns_df
        .groupby("Country")
        .agg(
            ReturnedUnits=(
                "ReturnQuantity",
                "sum"
            ),
            ReturnValue=(
                "ReturnValue",
                "sum"
            ),
            ReturnTransactions=(
                "InvoiceNo",
                "nunique"
            ),
        )
        .sort_values(
            "ReturnValue",
            ascending=False
        )
        .head(top_n)
        .reset_index()
    )

    countries["ReturnValue"] = (
        countries["ReturnValue"].round(2)
    )

    return countries.to_dict(
        orient="records"
    )


def build_returns_report(
    df_raw: pd.DataFrame,
    month: str | None = None,
    top_n: int = 5
) -> dict:
    returns_df = prepare_returns_data(
        df_raw
    )

    if month is not None:
        returns_df = returns_df[
            returns_df["Month"] == month
        ].copy()

        if returns_df.empty:
            raise ValueError(
                f"No return data found for month: {month}"
            )

    return {
        "period": (
            month
            if month is not None
            else "full_dataset"
        ),
        "kpis": calculate_return_kpis(
            returns_df
        ),
        "top_returned_products": (
            get_top_returned_products(
                returns_df,
                top_n
            )
        ),
        "top_return_countries": (
            get_top_return_countries(
                returns_df,
                top_n
            )
        ),
    }