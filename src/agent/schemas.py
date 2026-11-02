from typing import Literal

from pydantic import BaseModel


class QueryIntent(BaseModel):
    intent: Literal[
        "revenue_change",
        "business_performance",
        "returns_analysis",
        "customer_contribution",
        "anomaly_analysis",
        "unknown",
    ]

    month: str | None = None
    previous_month: str | None = None