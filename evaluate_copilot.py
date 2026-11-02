import json
import time
from pathlib import Path

import requests

API_URL = "http://127.0.0.1:8000/ask"

TEST_CASES = [
    {
        "question": "How did September 2011 perform?",
        "expected_intent": "business_performance",
        "expected_plan": ["business_performance"],
    },
    {
        "question": "How did October 2011 perform?",
        "expected_intent": "business_performance",
        "expected_plan": ["business_performance"],
    },
    {
        "question": "Show me the business performance for August 2011.",
        "expected_intent": "business_performance",
        "expected_plan": ["business_performance"],
    },
    {
        "question": "What were the key business metrics in November 2011?",
        "expected_intent": "business_performance",
        "expected_plan": ["business_performance"],
    },
    {
        "question": "Why did revenue fall from March 2011 to April 2011?",
        "expected_intent": "revenue_change",
        "expected_plan": ["revenue_change"],
    },
    {
        "question": "How did revenue change from January 2011 to February 2011?",
        "expected_intent": "revenue_change",
        "expected_plan": ["revenue_change"],
    },
    {
        "question": "Compare revenue performance from August 2011 to September 2011.",
        "expected_intent": "revenue_change",
        "expected_plan": ["revenue_change"],
    },
    {
        "question": "What changed between September 2011 and October 2011?",
        "expected_intent": "revenue_change",
        "expected_plan": ["revenue_change"],
    },
    {
        "question": "Which customers contributed most to the decline from March 2011 to April 2011?",
        "expected_intent": "customer_contribution",
        "expected_plan": ["customer_contribution"],
    },
    {
        "question": "Which customers drove the revenue change from January 2011 to February 2011?",
        "expected_intent": "customer_contribution",
        "expected_plan": ["customer_contribution"],
    },
    {
        "question": "Who contributed most to the decline from June 2011 to July 2011?",
        "expected_intent": "customer_contribution",
        "expected_plan": ["customer_contribution"],
    },
    {
        "question": "Which customers contributed most to the change from September 2011 to October 2011?",
        "expected_intent": "customer_contribution",
        "expected_plan": ["customer_contribution"],
    },
    {
        "question": "What were the returns in April 2011?",
        "expected_intent": "returns_analysis",
        "expected_plan": ["returns_analysis"],
    },
    {
        "question": "How many returns were recorded in September 2011?",
        "expected_intent": "returns_analysis",
        "expected_plan": ["returns_analysis"],
    },
    {
        "question": "Analyze returns for October 2011.",
        "expected_intent": "returns_analysis",
        "expected_plan": ["returns_analysis"],
    },
    {
        "question": "What was the return activity in November 2011?",
        "expected_intent": "returns_analysis",
        "expected_plan": ["returns_analysis"],
    },
    {
        "question": "Was April 2011 unusually weak?",
        "expected_intent": "anomaly_analysis",
        "expected_plan": ["anomaly_analysis"],
    },
    {
        "question": "Was November 2011 an unusual month?",
        "expected_intent": "anomaly_analysis",
        "expected_plan": ["anomaly_analysis"],
    },
    {
        "question": "Why did revenue fall from March 2011 to April 2011, and was April unusually weak?",
        "expected_intent": "anomaly_analysis",
        "expected_plan": [
            "revenue_change",
            "anomaly_analysis",
        ],
    },
    {
        "question": "Why did revenue fall from March 2011 to April 2011, and which customers contributed most?",
        "expected_intent": "revenue_change",
        "expected_plan": [
            "revenue_change",
            "customer_contribution",
        ],
    },
]


def normalize_list(value):
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value]

    if isinstance(value, tuple):
        return [str(item) for item in value]

    if isinstance(value, str):
        return [value]

    return []


def get_value(data, keys, default=None):
    if not isinstance(data, dict):
        return default

    for key in keys:
        if key in data:
            return data[key]

    for value in data.values():
        if isinstance(value, dict):
            found = get_value(
                value,
                keys,
                default=None,
            )

            if found is not None:
                return found

    return default


def extract_intent(data):
    intent = get_value(
        data,
        [
            "intent",
            "router_intent",
            "detected_intent",
        ],
    )

    if isinstance(intent, dict):
        intent = intent.get(
            "intent"
        )

    return intent


def extract_plan(data):
    plan = get_value(
        data,
        [
            "plan",
            "execution_plan",
        ],
        default=[],
    )

    return normalize_list(plan)


def extract_completed_tools(data):
    tools = get_value(
        data,
        [
            "completed_tools",
            "tools_executed",
            "executed_tools",
        ],
        default=[],
    )

    return normalize_list(tools)


def extract_verification(data):
    verification = get_value(
        data,
        [
            "answer_verification",
            "verification",
        ],
        default={},
    )

    if not isinstance(
        verification,
        dict,
    ):
        return False, None

    passed = verification.get(
        "passed",
        False,
    )

    source = verification.get(
        "source"
    )

    return bool(passed), source


def compare_tools(
    actual,
    expected,
):
    return set(actual) == set(expected)


def compare_plan(
    actual,
    expected,
):
    return actual == expected


def run_case(
    index,
    case,
):
    question = case[
        "question"
    ]

    expected_intent = case[
        "expected_intent"
    ]

    expected_plan = case[
        "expected_plan"
    ]

    start = time.perf_counter()

    try:
        response = requests.post(
            API_URL,
            json={
                "question": question
            },
            timeout=600,
        )

        latency = (
            time.perf_counter()
            - start
        )

        response.raise_for_status()

        data = response.json()

        if data.get(
            "needs_clarification",
            False,
        ):
            return {
                "id": index,
                "question": question,
                "status": "clarification",
                "expected_intent": expected_intent,
                "actual_intent": None,
                "intent_correct": False,
                "expected_plan": expected_plan,
                "actual_plan": [],
                "plan_correct": False,
                "completed_tools": [],
                "tools_correct": False,
                "verified": False,
                "fallback": False,
                "latency_seconds": round(
                    latency,
                    2,
                ),
                "error": None,
            }

        actual_intent = extract_intent(
            data
        )

        actual_plan = extract_plan(
            data
        )

        completed_tools = (
            extract_completed_tools(
                data
            )
        )

        verified, source = (
            extract_verification(
                data
            )
        )

        fallback = (
            source
            == "safe_fallback"
        )

        intent_correct = (
            actual_intent
            == expected_intent
        )

        plan_correct = compare_plan(
            actual_plan,
            expected_plan,
        )

        tools_correct = compare_tools(
            completed_tools,
            expected_plan,
        )

        return {
            "id": index,
            "question": question,
            "status": "success",
            "expected_intent": expected_intent,
            "actual_intent": actual_intent,
            "intent_correct": intent_correct,
            "expected_plan": expected_plan,
            "actual_plan": actual_plan,
            "plan_correct": plan_correct,
            "completed_tools": completed_tools,
            "tools_correct": tools_correct,
            "verified": verified,
            "fallback": fallback,
            "latency_seconds": round(
                latency,
                2,
            ),
            "error": None,
        }

    except Exception as exc:
        latency = (
            time.perf_counter()
            - start
        )

        return {
            "id": index,
            "question": question,
            "status": "error",
            "expected_intent": expected_intent,
            "actual_intent": None,
            "intent_correct": False,
            "expected_plan": expected_plan,
            "actual_plan": [],
            "plan_correct": False,
            "completed_tools": [],
            "tools_correct": False,
            "verified": False,
            "fallback": False,
            "latency_seconds": round(
                latency,
                2,
            ),
            "error": str(exc),
        }


def percentage(
    count,
    total,
):
    if total == 0:
        return 0.0

    return round(
        count / total * 100,
        2,
    )


def main():
    print()
    print(
        "Agentic AI Decision Copilot"
    )
    print(
        "Evaluation Benchmark"
    )
    print(
        "=" * 60
    )

    results = []

    for index, case in enumerate(
        TEST_CASES,
        start=1,
    ):
        print()
        print(
            f"[{index}/{len(TEST_CASES)}] "
            f"{case['question']}"
        )

        result = run_case(
            index,
            case,
        )

        results.append(
            result
        )

        print(
            f"Status: "
            f"{result['status']}"
        )

        print(
            f"Intent: "
            f"{result['actual_intent']} "
            f"| Expected: "
            f"{result['expected_intent']}"
        )

        print(
            f"Plan: "
            f"{result['actual_plan']}"
        )

        print(
            f"Tools: "
            f"{result['completed_tools']}"
        )

        print(
            f"Verified: "
            f"{result['verified']}"
        )

        print(
            f"Fallback: "
            f"{result['fallback']}"
        )

        print(
            f"Latency: "
            f"{result['latency_seconds']}s"
        )

        if result[
            "error"
        ]:
            print(
                f"Error: "
                f"{result['error']}"
            )

    total = len(
        results
    )

    successful = sum(
        result["status"]
        == "success"
        for result in results
    )

    intent_correct = sum(
        result[
            "intent_correct"
        ]
        for result in results
    )

    plan_correct = sum(
        result[
            "plan_correct"
        ]
        for result in results
    )

    tools_correct = sum(
        result[
            "tools_correct"
        ]
        for result in results
    )

    verified = sum(
        result[
            "verified"
        ]
        for result in results
    )

    fallbacks = sum(
        result[
            "fallback"
        ]
        for result in results
    )

    errors = sum(
        result["status"]
        == "error"
        for result in results
    )

    clarifications = sum(
        result["status"]
        == "clarification"
        for result in results
    )

    latencies = [
        result[
            "latency_seconds"
        ]
        for result in results
        if result[
            "status"
        ] == "success"
    ]

    average_latency = (
        round(
            sum(latencies)
            / len(latencies),
            2,
        )
        if latencies
        else 0.0
    )

    summary = {
        "total_questions": total,
        "successful_requests": successful,
        "errors": errors,
        "unexpected_clarifications": clarifications,
        "routing_accuracy_percent": percentage(
            intent_correct,
            total,
        ),
        "plan_accuracy_percent": percentage(
            plan_correct,
            total,
        ),
        "tool_selection_accuracy_percent": percentage(
            tools_correct,
            total,
        ),
        "verified_answer_rate_percent": percentage(
            verified,
            total,
        ),
        "fallback_rate_percent": percentage(
            fallbacks,
            total,
        ),
        "average_latency_seconds": average_latency,
    }

    output = {
        "summary": summary,
        "results": results,
    }

    Path(
        "evaluation_results.json"
    ).write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "=" * 60
    )
    print(
        "FINAL RESULTS"
    )
    print(
        "=" * 60
    )

    print(
        f"Questions: {total}"
    )

    print(
        f"Successful requests: "
        f"{successful}/{total}"
    )

    print(
        f"Routing accuracy: "
        f"{summary['routing_accuracy_percent']}%"
    )

    print(
        f"Plan accuracy: "
        f"{summary['plan_accuracy_percent']}%"
    )

    print(
        f"Tool selection accuracy: "
        f"{summary['tool_selection_accuracy_percent']}%"
    )

    print(
        f"Verified answer rate: "
        f"{summary['verified_answer_rate_percent']}%"
    )

    print(
        f"Fallback rate: "
        f"{summary['fallback_rate_percent']}%"
    )

    print(
        f"Average latency: "
        f"{summary['average_latency_seconds']}s"
    )

    print(
        f"Errors: {errors}"
    )

    print(
        f"Unexpected clarifications: "
        f"{clarifications}"
    )

    print()
    print(
        "Detailed results saved to:"
    )

    print(
        "evaluation_results.json"
    )


if __name__ == "__main__":
    main()