def value_variants(
    value
) -> set[str]:
    variants = {
        str(value)
    }

    if isinstance(
        value,
        float,
    ):
        variants.add(
            f"{value:.2f}"
        )

        variants.add(
            f"{value:,.2f}"
        )

        if value.is_integer():
            variants.add(
                str(int(value))
            )

    if isinstance(
        value,
        int,
    ):
        variants.add(
            f"{value:,}"
        )

    return variants


def value_appears(
    answer: str,
    value,
) -> bool:
    answer_lower = answer.lower()

    variants = value_variants(
        value
    )

    return any(
        variant.lower() in answer_lower
        for variant in variants
    )


def verify_answer_quality(
    answer: str,
    intent: str,
    tool_result: dict,
) -> dict:
    missing_requirements = []

    if intent == "business_performance":
        kpis = tool_result.get(
            "kpis",
            {}
        )

        required_values = {
            "revenue": kpis.get(
                "revenue"
            ),
            "orders": kpis.get(
                "orders"
            ),
            "customers": kpis.get(
                "customers"
            ),
            "average_order_value": kpis.get(
                "average_order_value"
            ),
        }

        for name, value in required_values.items():
            if value is None:
                continue

            if not value_appears(
                answer,
                value,
            ):
                missing_requirements.append(
                    name
                )

    elif intent == "revenue_change":
        metrics = tool_result.get(
            "metrics",
            {}
        )

        changes = metrics.get(
            "percentage_changes",
            {}
        )

        required_values = {
            "revenue_change": changes.get(
                "revenue"
            ),
            "orders_change": changes.get(
                "orders"
            ),
            "customers_change": changes.get(
                "customers"
            ),
            "average_order_value_change": changes.get(
                "average_order_value"
            ),
        }

        for name, value in required_values.items():
            if value is None:
                continue

            if not value_appears(
                answer,
                value,
            ):
                missing_requirements.append(
                    name
                )

    elif intent == "returns_analysis":
        kpis = tool_result.get(
            "kpis",
            {}
        )

        required_values = {
            "return_transactions": kpis.get(
                "return_transactions"
            ),
            "returned_units": kpis.get(
                "returned_units"
            ),
            "return_value": kpis.get(
                "return_value"
            ),
        }

        for name, value in required_values.items():
            if value is None:
                continue

            if not value_appears(
                answer,
                value,
            ):
                missing_requirements.append(
                    name
                )

    elif intent == "customer_contribution":
        declines = tool_result.get(
            "top_customer_declines",
            []
        )

        if not declines:
            missing_requirements.append(
                "customer_declines"
            )

        else:
            top_customers = declines[:2]

            for index, customer in enumerate(
                top_customers,
                start=1,
            ):
                customer_id = customer.get(
                    "CustomerID"
                )

                revenue_change = customer.get(
                    "revenue_change"
                )

                if (
                    customer_id is not None
                    and not value_appears(
                        answer,
                        customer_id,
                    )
                ):
                    missing_requirements.append(
                        f"customer_{index}_id"
                    )

                if (
                    revenue_change is not None
                    and not value_appears(
                        answer,
                        revenue_change,
                    )
                ):
                    missing_requirements.append(
                        f"customer_{index}_revenue_change"
                    )

    elif intent == "anomaly_analysis":
        if "error" in tool_result:
            missing_requirements.append(
                "valid_anomaly_result"
            )

        elif "period" in tool_result:
            period = tool_result.get(
                "period"
            )

            z_scores = tool_result.get(
                "z_scores",
                {}
            )

            anomalies = tool_result.get(
                "anomalies",
                {}
            )

            revenue_z = z_scores.get(
                "revenue"
            )

            revenue_status = anomalies.get(
                "revenue"
            )

            if (
                period is not None
                and str(period) not in answer
            ):
                missing_requirements.append(
                    "period"
                )

            if (
                revenue_z is not None
                and not value_appears(
                    answer,
                    revenue_z,
                )
            ):
                missing_requirements.append(
                    "revenue_z_score"
                )

            if (
                revenue_status is not None
                and revenue_status.lower()
                not in answer.lower()
            ):
                missing_requirements.append(
                    "revenue_anomaly_status"
                )

        else:
            anomalous_months = tool_result.get(
                "anomalous_months",
                []
            )

            if not anomalous_months:
                missing_requirements.append(
                    "anomalous_months"
                )

            else:
                first_month = anomalous_months[0]

                month = first_month.get(
                    "Month"
                )

                if (
                    month is not None
                    and str(month) not in answer
                ):
                    missing_requirements.append(
                        "first_anomalous_month"
                    )

    else:
        return {
            "passed": True,
            "missing_requirements": [],
        }

    passed = (
        len(missing_requirements) == 0
    )

    return {
        "passed": passed,
        "missing_requirements": (
            missing_requirements
        ),
    }