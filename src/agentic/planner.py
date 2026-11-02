import json
import re

from src.llm.shared_model import generate_text


AVAILABLE_TOOLS = [
    "business_performance",
    "revenue_change",
    "returns_analysis",
    "customer_contribution",
    "anomaly_analysis",
]


PREFERRED_TOOL_ORDER = [
    "business_performance",
    "revenue_change",
    "customer_contribution",
    "returns_analysis",
    "anomaly_analysis",
]


def extract_json_object(
    text: str
) -> dict:
    text = (
        text
        .strip()
        .replace(
            "```json",
            ""
        )
        .replace(
            "```",
            ""
        )
    )

    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if not match:
        raise ValueError(
            "No JSON object found."
        )

    return json.loads(
        match.group(0)
    )


def build_planner_prompt(
    question: str,
    month: str | None,
    previous_month: str | None,
) -> str:
    return f"""
You are a planning agent for a business analytics copilot.

Your job is to choose ONLY the analytics tools required
to fully answer the user's question.

Do not add tools that are unrelated to the question.

AVAILABLE TOOLS:

business_performance
Use for monthly business KPIs and general performance.

revenue_change
Use when comparing revenue or KPI changes between periods.

returns_analysis
Use ONLY when the user asks about returns,
returned products, cancellations, or refunds.

customer_contribution
Use ONLY when the user asks which customers contributed
to revenue growth or decline.

anomaly_analysis
Use ONLY when the user asks whether performance was unusual,
anomalous, abnormal, unexpected, or an outlier.

A question may require multiple tools,
but never add a tool without evidence in the question.

Examples:

Question:
How did September 2011 perform?

Answer:
{{
  "tools": [
    "business_performance"
  ]
}}

Question:
Why did revenue fall from March to April?

Answer:
{{
  "tools": [
    "revenue_change"
  ]
}}

Question:
Why did revenue fall from March to April
and which customers contributed most?

Answer:
{{
  "tools": [
    "revenue_change",
    "customer_contribution"
  ]
}}

Question:
Why did revenue fall from March to April
and was April unusually weak?

Answer:
{{
  "tools": [
    "revenue_change",
    "anomaly_analysis"
  ]
}}

Question:
How did April perform and what were the biggest returns?

Answer:
{{
  "tools": [
    "business_performance",
    "returns_analysis"
  ]
}}

Detected context:
month = {month}
previous_month = {previous_month}

User question:
{question}

Return ONLY valid JSON:

{{
  "tools": [
    "tool_name"
  ]
}}
""".strip()


def detect_required_tools(
    question: str
) -> list[str]:
    q = question.lower()

    detected = []

    revenue_terms = [
        "revenue fall",
        "revenue fell",
        "revenue decline",
        "revenue dropped",
        "revenue drop",
        "revenue decrease",
        "revenue increased",
        "revenue increase",
        "revenue growth",
        "revenue change",
        "why did revenue",
        "why revenue",
    ]

    customer_terms = [
        "customer",
        "customers",
        "client",
        "clients",
    ]

    contribution_terms = [
        "contributed",
        "contribute",
        "contribution",
        "drove",
        "driver",
        "drivers",
        "biggest contributors",
        "largest contributors",
        "lost the most",
        "declined the most",
    ]

    returns_terms = [
        "return",
        "returns",
        "returned",
        "refund",
        "refunds",
        "cancelled",
        "canceled",
        "cancellation",
        "cancellations",
    ]

    performance_terms = [
        "perform",
        "performed",
        "performance",
        "kpi",
        "kpis",
        "how did",
        "overall performance",
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
        "unusually weak",
        "unusually strong",
        "unusually high",
        "unusually low",
    ]

    has_revenue_change = any(
        term in q
        for term in revenue_terms
    )

    has_customer = any(
        term in q
        for term in customer_terms
    )

    has_contribution = any(
        term in q
        for term in contribution_terms
    )

    has_returns = any(
        term in q
        for term in returns_terms
    )

    has_performance = any(
        term in q
        for term in performance_terms
    )

    has_anomaly = any(
        term in q
        for term in anomaly_terms
    )

    if has_performance:
        detected.append(
            "business_performance"
        )

    if has_revenue_change:
        detected.append(
            "revenue_change"
        )

    if (
        has_customer
        and has_contribution
    ):
        detected.append(
            "customer_contribution"
        )

    if has_returns:
        detected.append(
            "returns_analysis"
        )

    if has_anomaly:
        detected.append(
            "anomaly_analysis"
        )

    return detected


def merge_plans(
    llm_tools: list[str],
    detected_tools: list[str],
) -> list[str]:
    """
    Hybrid planning guardrail.

    Deterministic detection has priority because it is
    grounded directly in explicit user intent.

    LLM tools are accepted only when deterministic
    detection found no usable tool at all.

    This prevents hallucinated but valid tool names,
    such as returns_analysis for a performance-only
    question.
    """

    if detected_tools:
        final_tools = detected_tools

    else:
        final_tools = [
            tool
            for tool in llm_tools
            if tool in AVAILABLE_TOOLS
        ]

    return [
        tool
        for tool in PREFERRED_TOOL_ORDER
        if tool in final_tools
    ]


def plan_question(
    question: str,
    month: str | None = None,
    previous_month: str | None = None,
) -> list[str]:
    raw_output = generate_text(
        prompt=build_planner_prompt(
            question=question,
            month=month,
            previous_month=previous_month,
        ),
        max_new_tokens=80,
    )

    print(
        "[PLANNER RAW OUTPUT]"
    )
    print(
        raw_output
    )

    try:
        parsed = extract_json_object(
            raw_output
        )

        llm_tools = [
            tool
            for tool in parsed.get(
                "tools",
                []
            )
            if tool in AVAILABLE_TOOLS
        ]

    except Exception as error:
        print(
            "[PLANNER] Could not parse LLM plan:",
            repr(error),
        )

        llm_tools = []

    detected_tools = detect_required_tools(
        question
    )

    final_tools = merge_plans(
        llm_tools=llm_tools,
        detected_tools=detected_tools,
    )

    print(
        "[LLM PLAN]",
        llm_tools,
    )

    print(
        "[DETERMINISTIC REQUIRED TOOLS]",
        detected_tools,
    )

    print(
        "[FINAL PLAN]",
        final_tools,
    )

    return final_tools