from src.agent.llm_router import route_question
from src.analytics.performance_analysis import (
    build_business_performance_report,
)
from src.analytics.revenue_analysis import (
    build_revenue_analysis_report,
)
from src.analytics.returns_analysis import (
    build_returns_report,
)


def execute_business_query(
    question: str,
    df_sales,
    df_raw,
) -> dict:
    intent = route_question(
        question
    )

    if intent.intent == "business_performance":
        if intent.month is None:
            return {
                "intent": intent.intent,
                "error": (
                    "A month is required for "
                    "business performance analysis."
                ),
            }

        result = build_business_performance_report(
            df_sales,
            month=intent.month,
        )

        return {
            "intent": intent.intent,
            "parameters": {
                "month": intent.month,
            },
            "result": result,
        }

    if intent.intent == "revenue_change":
        if (
            intent.month is None
            or intent.previous_month is None
        ):
            return {
                "intent": intent.intent,
                "error": (
                    "Two months are required for "
                    "revenue change analysis."
                ),
            }

        result = build_revenue_analysis_report(
            df_sales,
            previous_month=intent.previous_month,
            current_month=intent.month,
        )

        return {
            "intent": intent.intent,
            "parameters": {
                "previous_month": intent.previous_month,
                "current_month": intent.month,
            },
            "result": result,
        }

    if intent.intent == "returns_analysis":
        if intent.month is None:
            return {
                "intent": intent.intent,
                "error": (
                    "A month is required for "
                    "returns analysis."
                ),
            }

        result = build_returns_report(
            df_raw,
            month=intent.month,
        )

        return {
            "intent": intent.intent,
            "parameters": {
                "month": intent.month,
            },
            "result": result,
        }

    return {
        "intent": "unknown",
        "error": (
            "The question could not be mapped "
            "to a supported business analysis."
        ),
    }