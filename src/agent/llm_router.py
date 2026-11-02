import json
import re
from datetime import datetime

from src.agent.schemas import QueryIntent
from src.llm.shared_model import generate_text


MONTHS = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}


def extract_json_object(
    text: str
) -> dict:
    text = text.strip()

    text = text.replace(
        "```json",
        ""
    )

    text = text.replace(
        "```",
        ""
    )

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError(
            "No JSON object found in router output."
        )

    parsed = json.loads(
        match.group(0)
    )

    for key in [
        "month",
        "previous_month",
    ]:
        value = parsed.get(key)

        if isinstance(value, str):
            if value.strip().lower() in {
                "null",
                "none",
                "",
            }:
                parsed[key] = None

    return parsed


def extract_months_from_question(
    question: str
) -> list[str]:
    question_lower = question.lower()

    found_months = []

    numeric_matches = re.findall(
        r"\b(20\d{2})-(0[1-9]|1[0-2])\b",
        question_lower,
    )

    for year, month in numeric_matches:
        found_months.append(
            f"{year}-{month}"
        )

    text_matches = re.findall(
        r"\b("
        + "|".join(MONTHS.keys())
        + r")\s+(20\d{2})\b",
        question_lower,
    )

    for month_name, year in text_matches:
        found_months.append(
            f"{year}-{MONTHS[month_name]}"
        )

    unique_months = []

    for month in found_months:
        if month not in unique_months:
            unique_months.append(
                month
            )

    return unique_months


def sort_months(
    months: list[str]
) -> list[str]:
    return sorted(
        months,
        key=lambda value: datetime.strptime(
            value,
            "%Y-%m",
        ),
    )


def deterministic_fallback(
    question: str,
    parsed: dict,
) -> dict:
    question_lower = question.lower()

    months = extract_months_from_question(
        question
    )

    previous_month = parsed.get(
        "previous_month"
    )

    current_month = parsed.get(
        "month"
    )

    if len(months) >= 2:
        sorted_months = sort_months(
            months
        )

        previous_month = sorted_months[0]
        current_month = sorted_months[-1]

    elif len(months) == 1:
        current_month = months[0]

    customer_terms = [
        "customer",
        "customers",
        "client",
        "clients",
        "who",
    ]

    contribution_terms = [
        "contributed",
        "contribute",
        "contribution",
        "drove",
        "drive",
        "driver",
        "decline",
        "drop",
        "increase",
        "growth",
        "lost",
        "biggest",
    ]

    return_terms = [
        "return",
        "returns",
        "returned",
        "cancellation",
        "cancelled",
        "canceled",
    ]

    performance_terms = [
        "perform",
        "performed",
        "performance",
        "kpi",
        "kpis",
        "how did",
    ]

    anomaly_terms = [
        "anomaly",
        "anomalous",
        "unusual",
        "unusually",
        "abnormal",
        "outlier",
        "outliers",
        "unexpected",
        "unexpectedly",
        "spike",
        "unusually high",
        "unusually low",
        "unusually weak",
        "unusually strong",
    ]

    revenue_change_terms = [
        "revenue fall",
        "revenue fell",
        "revenue decline",
        "revenue drop",
        "revenue decrease",
        "revenue increase",
        "revenue growth",
        "revenue change",
        "why did revenue",
        "why revenue",
        "fell",
        "fall",
        "decline",
        "drop",
    ]

    has_customer_term = any(
        term in question_lower
        for term in customer_terms
    )

    has_contribution_term = any(
        term in question_lower
        for term in contribution_terms
    )

    has_return_term = any(
        term in question_lower
        for term in return_terms
    )

    has_performance_term = any(
        term in question_lower
        for term in performance_terms
    )

    has_anomaly_term = any(
        term in question_lower
        for term in anomaly_terms
    )

    has_revenue_change_term = any(
        term in question_lower
        for term in revenue_change_terms
    )

    if has_anomaly_term:
        return {
            "intent": "anomaly_analysis",
            "month": current_month,
            "previous_month": previous_month,
        }

    if (
        has_customer_term
        and has_contribution_term
        and previous_month is not None
        and current_month is not None
    ):
        return {
            "intent": "customer_contribution",
            "month": current_month,
            "previous_month": previous_month,
        }

    if has_return_term:
        return {
            "intent": "returns_analysis",
            "month": current_month,
            "previous_month": previous_month,
        }

    if (
        has_revenue_change_term
        and previous_month is not None
        and current_month is not None
    ):
        return {
            "intent": "revenue_change",
            "month": current_month,
            "previous_month": previous_month,
        }

    if has_performance_term:
        return {
            "intent": "business_performance",
            "month": current_month,
            "previous_month": previous_month,
        }

    return {
        "intent": parsed.get(
            "intent",
            "unknown",
        ),
        "month": current_month,
        "previous_month": previous_month,
    }


def build_router_prompt(
    question: str
) -> str:
    return f"""
You are a business analytics routing agent.

Classify the question into exactly one primary intent.

AVAILABLE INTENTS:

business_performance
Use for overall monthly performance and KPIs.

revenue_change
Use for overall revenue change between two months.

returns_analysis
Use for product returns and cancellations.

customer_contribution
Use when the user asks which customers contributed
to revenue growth or decline.

anomaly_analysis
Use when the user asks whether performance was unusual,
anomalous, abnormal, an outlier, unexpectedly high,
or unexpectedly low.

unknown
Use only if none apply.

Always preserve all months mentioned.

If two months are present:
month = later month
previous_month = earlier month

Examples:

Question:
Was November 2011 anomalous?

Answer:
{{
  "intent": "anomaly_analysis",
  "month": "2011-11",
  "previous_month": null
}}

Question:
Why did revenue fall from March 2011 to April 2011,
and was April unusually weak?

Answer:
{{
  "intent": "anomaly_analysis",
  "month": "2011-04",
  "previous_month": "2011-03"
}}

Question:
Which customers contributed most to the revenue decline
from March 2011 to April 2011?

Answer:
{{
  "intent": "customer_contribution",
  "month": "2011-04",
  "previous_month": "2011-03"
}}

Question:
How did September 2011 perform?

Answer:
{{
  "intent": "business_performance",
  "month": "2011-09",
  "previous_month": null
}}

Return ONLY valid JSON.

Schema:

{{
  "intent": "business_performance | revenue_change | returns_analysis | customer_contribution | anomaly_analysis | unknown",
  "month": "YYYY-MM or null",
  "previous_month": "YYYY-MM or null"
}}

User question:
{question}
""".strip()


def route_question(
    question: str
) -> QueryIntent:
    raw_output = generate_text(
        prompt=build_router_prompt(
            question
        ),
        max_new_tokens=100,
    )

    print(
        "[LLM ROUTER RAW OUTPUT]"
    )
    print(
        raw_output
    )

    try:
        parsed = extract_json_object(
            raw_output
        )

    except Exception:
        parsed = {
            "intent": "unknown",
            "month": None,
            "previous_month": None,
        }

    parsed = deterministic_fallback(
        question=question,
        parsed=parsed,
    )

    print(
        "[FINAL ROUTER DECISION]",
        parsed,
    )

    return QueryIntent(
        **parsed
    )