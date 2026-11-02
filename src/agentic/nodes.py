from typing import Any

from src.agent.answer_generator import generate_business_answer
from src.agent.llm_router import route_question
from src.analytics.anomaly_analysis import (
    analyze_specific_month,
    build_anomaly_report,
)
from src.analytics.customer_analysis import (
    build_customer_contribution_report,
)
from src.analytics.performance_analysis import (
    build_business_performance_report,
)
from src.analytics.returns_analysis import (
    build_returns_report,
)
from src.analytics.revenue_analysis import (
    build_revenue_analysis_report,
)
from src.agentic.answer_verifier import verify_answer_numbers
from src.agentic.planner import plan_question
from src.agentic.quality_verifier import verify_answer_quality


def route_query(
    state: dict[str, Any]
) -> dict[str, Any]:
    question = state["question"]

    route = route_question(
        question
    )

    state["intent"] = route.intent
    state["month"] = route.month
    state["previous_month"] = (
        route.previous_month
    )

    print(
        "[ROUTER]",
        state["intent"],
        state["month"],
        state["previous_month"],
    )

    return state


def create_plan(
    state: dict[str, Any]
) -> dict[str, Any]:
    question = state["question"]

    plan = plan_question(
        question=question,
        month=state.get("month"),
        previous_month=state.get(
            "previous_month"
        ),
    )

    state["plan"] = plan
    state["current_step"] = 0
    state["completed_tools"] = []

    print(
        "[AGENT PLAN]",
        plan,
    )

    return state


def execute_named_tool(
    tool_name: str,
    state: dict[str, Any],
    df_sales,
    df_raw,
) -> dict[str, Any]:
    month = state.get(
        "month"
    )

    previous_month = state.get(
        "previous_month"
    )

    if tool_name == "business_performance":
        if month is None:
            raise ValueError(
                "business_performance requires month."
            )

        return build_business_performance_report(
            df=df_sales,
            month=month,
        )

    if tool_name == "revenue_change":
        if (
            previous_month is None
            or month is None
        ):
            raise ValueError(
                "revenue_change requires "
                "previous_month and month."
            )

        return build_revenue_analysis_report(
            df=df_sales,
            previous_month=previous_month,
            current_month=month,
        )

    if tool_name == "returns_analysis":
        if month is None:
            raise ValueError(
                "returns_analysis requires month."
            )

        return build_returns_report(
            df_raw,
            month,
        )

    if tool_name == "customer_contribution":
        if (
            previous_month is None
            or month is None
        ):
            raise ValueError(
                "customer_contribution requires "
                "previous_month and month."
            )

        return build_customer_contribution_report(
            df=df_sales,
            previous_month=previous_month,
            current_month=month,
        )

    if tool_name == "anomaly_analysis":
        if month is not None:
            return analyze_specific_month(
                df=df_sales,
                month=month,
                threshold=1.5,
            )

        return build_anomaly_report(
            df=df_sales,
            threshold=1.5,
        )

    raise ValueError(
        f"Unknown tool: {tool_name}"
    )


def execute_tool(
    state: dict[str, Any],
    df_sales,
    df_raw,
) -> dict[str, Any]:
    plan = state.get(
        "plan",
        [],
    )

    if not plan:
        state["tool_result"] = {}
        state["tool_results"] = {}
        state["verification_passed"] = False

        print(
            "[SINGLE-STEP] No tool available."
        )

        return state

    tool_name = plan[0]

    print(
        "[SINGLE-STEP] Executing:",
        tool_name,
    )

    result = execute_named_tool(
        tool_name=tool_name,
        state=state,
        df_sales=df_sales,
        df_raw=df_raw,
    )

    state["tool_result"] = result
    state["tool_results"] = {
        tool_name: result
    }

    state["completed_tools"] = [
        tool_name
    ]

    state["current_step"] = 1

    print(
        "[SINGLE-STEP] Tool result:",
        result,
    )

    return state


def execute_next_tool(
    state: dict[str, Any],
    df_sales,
    df_raw,
) -> dict[str, Any]:
    plan = state.get(
        "plan",
        [],
    )

    current_step = state.get(
        "current_step",
        0,
    )

    if current_step >= len(plan):
        print(
            "[MULTI-STEP] No remaining tools."
        )
        return state

    tool_name = plan[
        current_step
    ]

    print(
        "[MULTI-STEP] Executing:",
        tool_name,
    )

    result = execute_named_tool(
        tool_name=tool_name,
        state=state,
        df_sales=df_sales,
        df_raw=df_raw,
    )

    tool_results = dict(
        state.get(
            "tool_results",
            {},
        )
    )

    tool_results[
        tool_name
    ] = result

    state["tool_results"] = (
        tool_results
    )

    completed_tools = list(
        state.get(
            "completed_tools",
            [],
        )
    )

    if tool_name not in completed_tools:
        completed_tools.append(
            tool_name
        )

    state["completed_tools"] = (
        completed_tools
    )

    state["current_step"] = (
        current_step + 1
    )

    print(
        "[MULTI-STEP] Completed:",
        state[
            "completed_tools"
        ],
    )

    return state


def decide_next_step(
    state: dict[str, Any]
) -> str:
    current_step = state.get(
        "current_step",
        0,
    )

    plan = state.get(
        "plan",
        [],
    )

    if current_step < len(plan):
        state[
            "needs_more_analysis"
        ] = True

        print(
            "[MULTI-STEP] "
            "More analysis required."
        )

        return "continue"

    state[
        "needs_more_analysis"
    ] = False

    print(
        "[MULTI-STEP] Plan completed."
    )

    return "verify"


def result_is_valid(
    result: Any
) -> bool:
    if result is None:
        return False

    if isinstance(
        result,
        dict,
    ):
        if not result:
            return False

        if "error" in result:
            return False

        return True

    return False


def verify_result(
    state: dict[str, Any]
) -> dict[str, Any]:
    tool_results = state.get(
        "tool_results",
        {},
    )

    if tool_results:
        invalid_tools = [
            tool_name
            for tool_name, result
            in tool_results.items()
            if not result_is_valid(
                result
            )
        ]

        if invalid_tools:
            state[
                "verification_passed"
            ] = False

            print(
                "[VERIFIER] Invalid tool results:",
                invalid_tools,
            )

            return state

        if len(tool_results) == 1:
            only_result = next(
                iter(
                    tool_results.values()
                )
            )

            state[
                "tool_result"
            ] = only_result

        else:
            state[
                "tool_result"
            ] = {
                "plan": state.get(
                    "plan",
                    [],
                ),
                "results": tool_results,
            }

        state[
            "verification_passed"
        ] = True

        print(
            "[VERIFIER] "
            "All planned tool results are valid."
        )

        return state

    tool_result = state.get(
        "tool_result",
        {},
    )

    if result_is_valid(
        tool_result
    ):
        state[
            "verification_passed"
        ] = True

        print(
            "[VERIFIER] "
            "Tool result is valid."
        )

    else:
        state[
            "verification_passed"
        ] = False

        print(
            "[VERIFIER] "
            "Tool result is invalid."
        )

    return state


def generate_answer(
    state: dict[str, Any]
) -> dict[str, Any]:
    plan = state.get(
        "plan",
        [],
    )

    if plan == ["customer_contribution"]:
        result = state.get(
            "tool_results",
            {},
        ).get(
            "customer_contribution",
            state.get(
                "tool_result",
                {},
            ),
        )

        state[
            "draft_answer"
        ] = build_customer_fallback(
            result
        )

        state[
            "answer_source"
        ] = "deterministic"

        print(
            "[ANSWER] Deterministic customer answer generated."
        )

        return state

    attempts = state.get(
        "generation_attempts",
        0,
    )

    attempts += 1

    state[
        "generation_attempts"
    ] = attempts

    state[
        "answer_source"
    ] = "llm"

    print(
        "[ANSWER] Generation attempt:",
        attempts,
    )

    draft_answer = (
        generate_business_answer(
            question=state[
                "question"
            ],
            tool_result=state[
                "tool_result"
            ],
        )
    )

    state[
        "draft_answer"
    ] = draft_answer

    return state


def verify_multi_step_quality(
    answer: str,
    plan: list[str],
    tool_results: dict[str, Any],
) -> dict[str, Any]:
    missing_requirements = []

    for tool_name in plan:
        tool_result = (
            tool_results.get(
                tool_name,
                {},
            )
        )

        quality_result = (
            verify_answer_quality(
                answer=answer,
                intent=tool_name,
                tool_result=tool_result,
            )
        )

        tool_missing = (
            quality_result.get(
                "missing_requirements",
                [],
            )
        )

        for requirement in tool_missing:
            missing_requirements.append(
                f"{tool_name}:{requirement}"
            )

    return {
        "passed": (
            len(
                missing_requirements
            )
            == 0
        ),
        "missing_requirements": (
            missing_requirements
        ),
    }


def verify_answer(
    state: dict[str, Any]
) -> dict[str, Any]:
    answer = state.get(
        "draft_answer",
        "",
    )

    tool_result = state.get(
        "tool_result",
        {},
    )

    numeric_verification = (
        verify_answer_numbers(
            answer=answer,
            tool_result=tool_result,
        )
    )

    plan = state.get(
        "plan",
        [],
    )

    tool_results = state.get(
        "tool_results",
        {},
    )

    if len(plan) > 1:
        quality_verification = (
            verify_multi_step_quality(
                answer=answer,
                plan=plan,
                tool_results=tool_results,
            )
        )

    else:
        intent = (
            plan[0]
            if plan
            else state.get(
                "intent",
                "unknown",
            )
        )

        single_result = (
            tool_results.get(
                intent,
                tool_result,
            )
        )

        quality_verification = (
            verify_answer_quality(
                answer=answer,
                intent=intent,
                tool_result=single_result,
            )
        )

    passed = (
        numeric_verification.get(
            "passed",
            False,
        )
        and quality_verification.get(
            "passed",
            False,
        )
    )

    verification = {
        "passed": passed,
        "source": state.get(
            "answer_source",
            "llm",
        ),
        "numeric": numeric_verification,
        "quality": quality_verification,
    }

    state[
        "answer_verification"
    ] = verification

    if passed:
        state[
            "final_answer"
        ] = answer

    print(
        "[ANSWER VERIFIER]",
        verification,
    )

    return state


def build_performance_fallback(
    result: dict[str, Any]
) -> str:
    period = result.get(
        "period",
        "unknown period",
    )

    kpis = result.get(
        "kpis",
        {},
    )

    revenue = kpis.get(
        "revenue",
        0,
    )

    orders = kpis.get(
        "orders",
        0,
    )

    customers = kpis.get(
        "customers",
        0,
    )

    aov = kpis.get(
        "average_order_value",
        0,
    )

    return (
        f"For {period}, revenue was "
        f"{revenue:,.2f}, with "
        f"{orders:,} orders and "
        f"{customers:,} customers. "
        f"Average order value was "
        f"{aov:,.2f}."
    )


def build_revenue_fallback(
    result: dict[str, Any]
) -> str:
    period = result.get(
        "period",
        {},
    )

    previous_month = period.get(
        "previous_month",
        "previous period",
    )

    current_month = period.get(
        "current_month",
        "current period",
    )

    metrics = result.get(
        "metrics",
        {},
    )

    previous = metrics.get(
        "previous",
        {},
    )

    current = metrics.get(
        "current",
        {},
    )

    pct_changes = result.get(
        "percentage_changes",
        result.get(
            "pct_changes",
            {},
        ),
    )

    def calculate_change(
        metric_name: str
    ) -> float:
        if metric_name in pct_changes:
            return float(
                pct_changes.get(
                    metric_name,
                    0,
                )
            )

        previous_value = previous.get(
            metric_name,
            0,
        )

        current_value = current.get(
            metric_name,
            0,
        )

        if not previous_value:
            return 0.0

        return (
            (current_value - previous_value)
            / previous_value
            * 100
        )

    revenue_change = calculate_change(
        "revenue"
    )

    orders_change = calculate_change(
        "orders"
    )

    customers_change = calculate_change(
        "customers"
    )

    quantity_change = calculate_change(
        "quantity"
    )

    if (
        "average_order_value"
        in pct_changes
    ):
        aov_change = float(
            pct_changes.get(
                "average_order_value",
                0,
            )
        )
    elif "aov" in pct_changes:
        aov_change = float(
            pct_changes.get(
                "aov",
                0,
            )
        )
    else:
        previous_aov = previous.get(
            "average_order_value",
            previous.get(
                "aov",
                0,
            ),
        )

        current_aov = current.get(
            "average_order_value",
            current.get(
                "aov",
                0,
            ),
        )

        if previous_aov:
            aov_change = (
                (current_aov - previous_aov)
                / previous_aov
                * 100
            )
        else:
            aov_change = 0.0

    return (
        f"Revenue changed by "
        f"{revenue_change:.2f}% from "
        f"{previous_month} to "
        f"{current_month}. "
        f"Orders changed by "
        f"{orders_change:.2f}%, "
        f"customers by "
        f"{customers_change:.2f}%, "
        f"quantity by "
        f"{quantity_change:.2f}%, "
        f"and average order value by "
        f"{aov_change:.2f}%."
    )


def build_returns_fallback(
    result: dict[str, Any]
) -> str:
    def find_value(data: Any, keys: tuple[str, ...], default=0):
        if isinstance(data, dict):
            for key in keys:
                if key in data and data[key] is not None:
                    return data[key]

            for value in data.values():
                found = find_value(value, keys, None)
                if found is not None:
                    return found

        elif isinstance(data, list):
            for item in data:
                found = find_value(item, keys, None)
                if found is not None:
                    return found

        return default

    period = find_value(
        result,
        ("period", "month"),
        "unknown period",
    )

    transactions = find_value(
        result,
        (
            "return_transactions",
            "returns_transactions",
            "transactions",
            "return_count",
            "returns_count",
        ),
        0,
    )

    units = find_value(
        result,
        (
            "returned_units",
            "return_units",
            "units_returned",
            "units",
        ),
        0,
    )

    value = find_value(
        result,
        (
            "return_value",
            "returns_value",
            "total_return_value",
            "returned_value",
            "value",
        ),
        0,
    )

    return (
        f"For {period}, there were "
        f"{int(transactions):,} return "
        f"transactions involving "
        f"{int(units):,} units, with total "
        f"return value "
        f"{float(value):,.2f}."
    )


def build_customer_fallback(
    result: dict[str, Any]
) -> str:
    period = result.get(
        "period",
        {},
    )

    previous_month = period.get(
        "previous_month",
        "previous period",
    )

    current_month = period.get(
        "current_month",
        "current period",
    )

    total_change = result.get(
        "total_revenue_change",
        0,
    )

    declines = result.get(
        "top_customer_declines",
        [],
    )

    combined_change = result.get(
        "top_declines_combined_change",
        0,
    )

    customer_parts = []

    for customer in declines[:5]:
        customer_id = customer.get(
            "CustomerID",
            customer.get(
                "customer_id",
                "unknown",
            ),
        )

        revenue_change = customer.get(
            "revenue_change",
            customer.get(
                "RevenueChange",
                customer.get(
                    "change",
                    0,
                ),
            ),
        )

        if isinstance(customer_id, float) and customer_id.is_integer():
            customer_id = int(customer_id)

        customer_parts.append(
            f"{customer_id}: "
            f"{revenue_change:,.2f}"
        )

    customers_text = "; ".join(
        customer_parts
    )

    return (
        f"From {previous_month} to "
        f"{current_month}, total revenue "
        f"changed by "
        f"{total_change:,.2f}. "
        f"The largest customer declines "
        f"were {customers_text}. "
        f"The top 10 declines combined "
        f"for {combined_change:,.2f} "
        f"of gross negative customer movement."
    )


def build_anomaly_fallback(
    result: dict[str, Any]
) -> str:
    if "metrics" in result:
        period = result.get(
            "period",
            "unknown period",
        )

        metrics = result.get(
            "metrics",
            {},
        )

        z_scores = result.get(
            "z_scores",
            {},
        )

        anomalies = result.get(
            "anomalies",
            {},
        )

        revenue = metrics.get(
            "revenue",
            0,
        )

        revenue_z = z_scores.get(
            "revenue",
            0,
        )

        revenue_status = (
            anomalies.get(
                "revenue",
                "unknown",
            )
        )

        orders_status = anomalies.get(
            "orders",
            "unknown",
        )

        customers_status = anomalies.get(
            "customers",
            "unknown",
        )

        quantity_status = anomalies.get(
            "quantity",
            "unknown",
        )

        aov_status = anomalies.get(
            "average_order_value",
            "unknown",
        )

        return (
            f"For {period}, revenue was "
            f"{revenue:,.2f} with a revenue "
            f"z-score of {revenue_z:.2f}. "
            f"Revenue was classified as "
            f"{revenue_status}. "
            f"Orders were classified as "
            f"{orders_status}, customers as "
            f"{customers_status}, quantity as "
            f"{quantity_status}, and average "
            f"order value as {aov_status}."
        )

    anomalous_months = result.get(
        "anomalous_months",
        [],
    )

    if not anomalous_months:
        return (
            "No anomalous months were detected "
            "using the configured threshold."
        )

    parts = []

    for month in anomalous_months:
        period = month.get(
            "period",
            "unknown",
        )

        anomalies = month.get(
            "anomalies",
            {},
        )

        statuses = [
            f"{metric}={status}"
            for metric, status
            in anomalies.items()
            if status != "normal"
        ]

        parts.append(
            f"{period}: "
            + ", ".join(
                statuses
            )
        )

    return (
        "Detected anomalous periods: "
        + "; ".join(parts)
        + "."
    )


def generate_safe_fallback(
    state: dict[str, Any]
) -> dict[str, Any]:
    plan = state.get(
        "plan",
        [],
    )

    tool_results = state.get(
        "tool_results",
        {},
    )

    fallback_parts = []

    for tool_name in plan:
        result = tool_results.get(
            tool_name,
            {},
        )

        if tool_name == "business_performance":
            fallback_parts.append(
                build_performance_fallback(
                    result
                )
            )

        elif tool_name == "revenue_change":
            fallback_parts.append(
                build_revenue_fallback(
                    result
                )
            )

        elif tool_name == "returns_analysis":
            fallback_parts.append(
                build_returns_fallback(
                    result
                )
            )

        elif tool_name == "customer_contribution":
            fallback_parts.append(
                build_customer_fallback(
                    result
                )
            )

        elif tool_name == "anomaly_analysis":
            fallback_parts.append(
                build_anomaly_fallback(
                    result
                )
            )

    if not fallback_parts:
        result = state.get(
            "tool_result",
            {},
        )

        intent = state.get(
            "intent",
            "unknown",
        )

        if intent == "business_performance":
            fallback_parts.append(
                build_performance_fallback(
                    result
                )
            )

        elif intent == "revenue_change":
            fallback_parts.append(
                build_revenue_fallback(
                    result
                )
            )

        elif intent == "returns_analysis":
            fallback_parts.append(
                build_returns_fallback(
                    result
                )
            )

        elif intent == "customer_contribution":
            fallback_parts.append(
                build_customer_fallback(
                    result
                )
            )

        elif intent == "anomaly_analysis":
            fallback_parts.append(
                build_anomaly_fallback(
                    result
                )
            )

    final_answer = " ".join(
        fallback_parts
    ).strip()

    if not final_answer:
        final_answer = (
            "The analysis completed, but a grounded "
            "final response could not be constructed."
        )

    state[
        "final_answer"
    ] = final_answer

    state[
        "answer_verification"
    ] = {
        "passed": True,
        "source": "safe_fallback",
        "numeric": {
            "passed": True,
            "unsupported_numbers": [],
        },
        "quality": {
            "passed": True,
            "missing_requirements": [],
        },
    }

    print(
        "[FALLBACK] Safe "
        + (
            "multi-step answer generated."
            if len(plan) > 1
            else "answer generated."
        )
    )

    return state


def route_after_answer_verification(
    state: dict[str, Any]
) -> str:
    verification = state.get(
        "answer_verification",
        {},
    )

    if verification.get(
        "passed",
        False,
    ):
        print(
            "[ANSWER ROUTER] "
            "Answer verified successfully."
        )

        return "finish"

    print(
        "[ANSWER ROUTER] "
        "First LLM answer failed verification. "
        "Switching directly to safe fallback."
    )

    return "fallback"