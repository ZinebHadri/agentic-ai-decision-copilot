import pandas as pd


def build_monthly_metrics(
    df: pd.DataFrame,
) -> pd.DataFrame:
    monthly = (
        df.groupby(
            "Month",
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
            customers=(
                "CustomerID",
                "nunique",
            ),
            quantity=(
                "Quantity",
                "sum",
            ),
        )
    )

    monthly[
        "average_order_value"
    ] = (
        monthly["revenue"]
        / monthly["orders"]
    )

    return monthly


def calculate_z_scores(
    series: pd.Series,
) -> pd.Series:
    std = series.std(
        ddof=0
    )

    if std == 0:
        return pd.Series(
            [0.0] * len(series),
            index=series.index,
        )

    return (
        series - series.mean()
    ) / std


def add_anomaly_scores(
    monthly: pd.DataFrame,
) -> pd.DataFrame:
    result = monthly.copy()

    metrics = [
        "revenue",
        "orders",
        "customers",
        "quantity",
        "average_order_value",
    ]

    for metric in metrics:
        result[
            f"{metric}_zscore"
        ] = calculate_z_scores(
            result[metric]
        )

    return result


def classify_anomaly(
    z_score: float,
    threshold: float,
) -> str:
    if z_score >= threshold:
        return "high"

    if z_score <= -threshold:
        return "low"

    return "normal"


def detect_month_anomalies(
    df: pd.DataFrame,
    threshold: float = 1.5,
) -> pd.DataFrame:
    monthly = build_monthly_metrics(
        df
    )

    scored = add_anomaly_scores(
        monthly
    )

    metrics = [
        "revenue",
        "orders",
        "customers",
        "quantity",
        "average_order_value",
    ]

    for metric in metrics:
        scored[
            f"{metric}_anomaly"
        ] = scored[
            f"{metric}_zscore"
        ].apply(
            lambda value: classify_anomaly(
                value,
                threshold,
            )
        )

    return scored


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


def build_anomaly_report(
    df: pd.DataFrame,
    threshold: float = 1.5,
) -> dict:
    scored = detect_month_anomalies(
        df=df,
        threshold=threshold,
    )

    anomaly_columns = [
        "revenue_anomaly",
        "orders_anomaly",
        "customers_anomaly",
        "quantity_anomaly",
        "average_order_value_anomaly",
    ]

    anomalous_mask = (
        scored[
            anomaly_columns
        ]
        .ne("normal")
        .any(
            axis=1
        )
    )

    anomalous_months = (
        scored[
            anomalous_mask
        ]
        .copy()
    )

    return {
        "threshold": threshold,
        "monthly_metrics": (
            dataframe_to_records(
                scored
            )
        ),
        "anomalous_months": (
            dataframe_to_records(
                anomalous_months
            )
        ),
    }


def analyze_specific_month(
    df: pd.DataFrame,
    month: str,
    threshold: float = 1.5,
) -> dict:
    scored = detect_month_anomalies(
        df=df,
        threshold=threshold,
    )

    selected = scored[
        scored["Month"] == month
    ]

    if selected.empty:
        return {
            "error": (
                f"No data found for month "
                f"{month}."
            )
        }

    row = selected.iloc[0]

    return {
        "period": month,
        "threshold": threshold,
        "metrics": {
            "revenue": round(
                float(
                    row["revenue"]
                ),
                2,
            ),
            "orders": int(
                row["orders"]
            ),
            "customers": int(
                row["customers"]
            ),
            "quantity": int(
                row["quantity"]
            ),
            "average_order_value": round(
                float(
                    row[
                        "average_order_value"
                    ]
                ),
                2,
            ),
        },
        "z_scores": {
            "revenue": round(
                float(
                    row[
                        "revenue_zscore"
                    ]
                ),
                2,
            ),
            "orders": round(
                float(
                    row[
                        "orders_zscore"
                    ]
                ),
                2,
            ),
            "customers": round(
                float(
                    row[
                        "customers_zscore"
                    ]
                ),
                2,
            ),
            "quantity": round(
                float(
                    row[
                        "quantity_zscore"
                    ]
                ),
                2,
            ),
            "average_order_value": round(
                float(
                    row[
                        "average_order_value_zscore"
                    ]
                ),
                2,
            ),
        },
        "anomalies": {
            "revenue": row[
                "revenue_anomaly"
            ],
            "orders": row[
                "orders_anomaly"
            ],
            "customers": row[
                "customers_anomaly"
            ],
            "quantity": row[
                "quantity_anomaly"
            ],
            "average_order_value": row[
                "average_order_value_anomaly"
            ],
        },
    }