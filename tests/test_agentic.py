import pytest

from src.agentic.answer_verifier import verify_answer_numbers
from src.agentic.quality_verifier import verify_answer_quality
from src.agentic.planner import (
    detect_required_tools,
    merge_plans,
)
from src.agentic.nodes import (
    generate_safe_fallback,
    route_after_answer_verification,
    decide_next_step,
)


def test_numeric_verifier_rejects_unsupported_number():
    tool_result = {
        "period": "2011-09",
        "kpis": {
            "revenue": 1056435.19,
            "orders": 1837,
            "customers": 1266,
            "average_order_value": 575.09,
        },
    }

    answer = (
        "Revenue was 10,564,351.19 "
        "with 1,837 orders."
    )

    result = verify_answer_numbers(
        answer=answer,
        tool_result=tool_result,
    )

    assert result["passed"] is False
    assert 10564351.19 in result["unsupported_numbers"]


def test_numeric_verifier_accepts_grounded_numbers():
    tool_result = {
        "period": "2011-09",
        "kpis": {
            "revenue": 1056435.19,
            "orders": 1837,
            "customers": 1266,
            "average_order_value": 575.09,
        },
    }

    answer = (
        "For 2011-09, revenue was 1,056,435.19 "
        "with 1,837 orders."
    )

    result = verify_answer_numbers(
        answer=answer,
        tool_result=tool_result,
    )

    assert result["passed"] is True
    assert result["unsupported_numbers"] == []


def test_quality_verifier_rejects_vague_revenue_change_answer():
    tool_result = {
        "period": {
            "previous_month": "2011-03",
            "current_month": "2011-04",
        },
        "metrics": {
            "percentage_changes": {
                "revenue": -25.03,
                "orders": -14.31,
                "quantity": -18.23,
                "customers": -12.11,
                "average_order_value": -12.51,
            }
        },
    }

    answer = (
        "Revenue fell from March 2011 to April 2011 "
        "because orders and customers declined."
    )

    result = verify_answer_quality(
        answer=answer,
        intent="revenue_change",
        tool_result=tool_result,
    )

    assert result["passed"] is False
    assert "revenue_change" in result["missing_requirements"]
    assert "orders_change" in result["missing_requirements"]
    assert "customers_change" in result["missing_requirements"]


def test_quality_verifier_accepts_complete_revenue_change_answer():
    tool_result = {
        "period": {
            "previous_month": "2011-03",
            "current_month": "2011-04",
        },
        "metrics": {
            "percentage_changes": {
                "revenue": -25.03,
                "orders": -14.31,
                "quantity": -18.23,
                "customers": -12.11,
                "average_order_value": -12.51,
            }
        },
    }

    answer = (
        "Revenue changed by -25.03%. "
        "Orders changed by -14.31%, "
        "customers by -12.11%, "
        "and average order value by -12.51%."
    )

    result = verify_answer_quality(
        answer=answer,
        intent="revenue_change",
        tool_result=tool_result,
    )

    assert result["passed"] is True
    assert result["missing_requirements"] == []


def test_customer_quality_verifier_rejects_missing_second_decline():
    tool_result = {
        "top_customer_declines": [
            {
                "CustomerID": 14646.0,
                "revenue_change": -18485.84,
            },
            {
                "CustomerID": 12415.0,
                "revenue_change": -16376.84,
            },
        ]
    }

    answer = (
        "Customer 14646 declined by -18,485.84. "
        "Customer 12415 was also a major contributor."
    )

    result = verify_answer_quality(
        answer=answer,
        intent="customer_contribution",
        tool_result=tool_result,
    )

    assert result["passed"] is False
    assert (
        "customer_2_revenue_change"
        in result["missing_requirements"]
    )


def test_customer_quality_verifier_accepts_top_two_customers():
    tool_result = {
        "top_customer_declines": [
            {
                "CustomerID": 14646.0,
                "revenue_change": -18485.84,
            },
            {
                "CustomerID": 12415.0,
                "revenue_change": -16376.84,
            },
        ]
    }

    answer = (
        "Customer 14646 declined by -18,485.84, "
        "while customer 12415 declined by -16,376.84."
    )

    result = verify_answer_quality(
        answer=answer,
        intent="customer_contribution",
        tool_result=tool_result,
    )

    assert result["passed"] is True
    assert result["missing_requirements"] == []


def test_safe_fallback_business_performance():
    state = {
        "question": "How did September 2011 perform?",
        "intent": "business_performance",
        "month": "2011-09",
        "previous_month": None,
        "plan": ["business_performance"],
        "current_step": 1,
        "completed_tools": ["business_performance"],
        "tool_result": {
            "period": "2011-09",
            "kpis": {
                "revenue": 1056435.19,
                "orders": 1837,
                "customers": 1266,
                "average_order_value": 575.09,
            },
        },
        "tool_results": {
            "business_performance": {
                "period": "2011-09",
                "kpis": {
                    "revenue": 1056435.19,
                    "orders": 1837,
                    "customers": 1266,
                    "average_order_value": 575.09,
                },
            },
        },
        "needs_more_analysis": False,
        "verification_passed": True,
        "draft_answer": "",
        "answer_verification": {},
        "generation_attempts": 2,
        "final_answer": "",
    }

    result = generate_safe_fallback(state)

    assert "1,056,435.19" in result["final_answer"]
    assert "1,837" in result["final_answer"]
    assert "1,266" in result["final_answer"]
    assert "575.09" in result["final_answer"]

    assert result["answer_verification"]["passed"] is True
    assert (
        result["answer_verification"]["source"]
        == "safe_fallback"
    )


def test_safe_fallback_revenue_change():
    state = {
        "question": (
            "Why did revenue fall from March 2011 "
            "to April 2011?"
        ),
        "intent": "revenue_change",
        "month": "2011-04",
        "previous_month": "2011-03",
        "plan": ["revenue_change"],
        "current_step": 1,
        "completed_tools": ["revenue_change"],
        "tool_result": {
            "period": {
                "previous_month": "2011-03",
                "current_month": "2011-04",
            },
            "metrics": {
                "previous": {
                    "revenue": 716215.26,
                    "orders": 1454,
                    "quantity": 376599,
                    "customers": 974,
                    "average_order_value": 492.58,
                },
                "current": {
                    "revenue": 536968.49,
                    "orders": 1246,
                    "quantity": 307953,
                    "customers": 856,
                    "average_order_value": 430.95,
                },
            },
        },
        "tool_results": {
            "revenue_change": {
                "period": {
                    "previous_month": "2011-03",
                    "current_month": "2011-04",
                },
                "metrics": {
                    "previous": {
                        "revenue": 716215.26,
                        "orders": 1454,
                        "quantity": 376599,
                        "customers": 974,
                        "average_order_value": 492.58,
                    },
                    "current": {
                        "revenue": 536968.49,
                        "orders": 1246,
                        "quantity": 307953,
                        "customers": 856,
                        "average_order_value": 430.95,
                    },
                },
            },
        },
        "needs_more_analysis": False,
        "verification_passed": True,
        "draft_answer": "",
        "answer_verification": {},
        "generation_attempts": 2,
        "final_answer": "",
    }

    result = generate_safe_fallback(state)

    assert "-25.03%" in result["final_answer"]
    assert "-14.31%" in result["final_answer"]
    assert "-18.23%" in result["final_answer"]
    assert "-12.11%" in result["final_answer"]
    assert "-12.51%" in result["final_answer"]

    assert result["answer_verification"]["passed"] is True


def test_safe_fallback_returns_analysis():
    state = {
        "question": (
            "Which products had the most returns "
            "in April 2011?"
        ),
        "intent": "returns_analysis",
        "month": "2011-04",
        "previous_month": None,
        "plan": ["returns_analysis"],
        "current_step": 1,
        "completed_tools": ["returns_analysis"],
        "tool_result": {
            "period": "2011-04",
            "metrics": {
                "return_transactions": 426,
                "returned_units": 23078,
                "return_value": 44601.50,
            },
        },
        "tool_results": {
            "returns_analysis": {
                "period": "2011-04",
                "metrics": {
                    "return_transactions": 426,
                    "returned_units": 23078,
                    "return_value": 44601.50,
                },
            },
        },
        "needs_more_analysis": False,
        "verification_passed": True,
        "draft_answer": "",
        "answer_verification": {},
        "generation_attempts": 2,
        "final_answer": "",
    }

    result = generate_safe_fallback(state)

    assert "426" in result["final_answer"]
    assert "23,078" in result["final_answer"]
    assert "44,601.50" in result["final_answer"]

    assert result["answer_verification"]["passed"] is True


def test_planner_detects_multi_step_question():
    question = (
        "Why did revenue fall from March 2011 to April 2011, "
        "and which customers contributed most?"
    )

    tools = detect_required_tools(
        question
    )

    assert "revenue_change" in tools
    assert "customer_contribution" in tools


def test_merge_plans_adds_missing_customer_tool():
    llm_tools = [
        "revenue_change"
    ]

    detected_tools = [
        "revenue_change",
        "customer_contribution",
    ]

    result = merge_plans(
        llm_tools=llm_tools,
        detected_tools=detected_tools,
    )

    assert result == [
        "revenue_change",
        "customer_contribution",
    ]


def test_decide_next_step_continues_when_plan_not_finished():
    state = {
        "current_step": 1,
        "plan": [
            "revenue_change",
            "customer_contribution",
        ],
    }

    result = decide_next_step(
        state
    )

    assert result == "continue"


def test_decide_next_step_verifies_when_plan_finished():
    state = {
        "current_step": 2,
        "plan": [
            "revenue_change",
            "customer_contribution",
        ],
    }

    result = decide_next_step(
        state
    )

    assert result == "verify"


def test_multi_step_safe_fallback_combines_results():
    state = {
        "question": (
            "Why did revenue fall from March 2011 "
            "to April 2011, and which customers "
            "contributed most?"
        ),
        "intent": "revenue_change",
        "month": "2011-04",
        "previous_month": "2011-03",
        "plan": [
            "revenue_change",
            "customer_contribution",
        ],
        "current_step": 2,
        "completed_tools": [
            "revenue_change",
            "customer_contribution",
        ],
        "tool_result": {},
        "tool_results": {
            "revenue_change": {
                "period": {
                    "previous_month": "2011-03",
                    "current_month": "2011-04",
                },
                "metrics": {
                    "previous": {
                        "revenue": 716215.26,
                        "orders": 1454,
                        "quantity": 376599,
                        "customers": 974,
                        "average_order_value": 492.58,
                    },
                    "current": {
                        "revenue": 536968.49,
                        "orders": 1246,
                        "quantity": 307953,
                        "customers": 856,
                        "average_order_value": 430.95,
                    },
                },
            },
            "customer_contribution": {
                "period": {
                    "previous_month": "2011-03",
                    "current_month": "2011-04",
                },
                "total_revenue_change": -179246.77,
                "top_declines_combined_change": -89993.47,
                "top_customer_declines": [
                    {
                        "CustomerID": 14646.0,
                        "revenue_change": -18485.84,
                    },
                    {
                        "CustomerID": 12415.0,
                        "revenue_change": -16376.84,
                    },
                    {
                        "CustomerID": 15769.0,
                        "revenue_change": -11649.96,
                    },
                    {
                        "CustomerID": 17450.0,
                        "revenue_change": -9915.46,
                    },
                    {
                        "CustomerID": 14156.0,
                        "revenue_change": -6746.44,
                    },
                ],
            },
        },
        "needs_more_analysis": False,
        "verification_passed": True,
        "draft_answer": "",
        "answer_verification": {},
        "generation_attempts": 2,
        "final_answer": "",
    }

    result = generate_safe_fallback(
        state
    )

    answer = result[
        "final_answer"
    ]

    assert "-25.03%" in answer
    assert "14646: -18,485.84" in answer
    assert "-18,485.84" in answer
    assert "12415: -16,376.84" in answer
    assert "-16,376.84" in answer

    assert (
        result[
            "answer_verification"
        ]["passed"]
        is True
    )


def test_router_uses_fallback_after_first_failed_attempt():
    state = {
        "answer_verification": {
            "passed": False
        },
        "generation_attempts": 1,
    }

    route = route_after_answer_verification(
        state
    )

    assert route == "fallback"


def test_router_uses_fallback_after_two_failed_attempts():
    state = {
        "answer_verification": {
            "passed": False
        },
        "generation_attempts": 2,
    }

    route = route_after_answer_verification(
        state
    )

    assert route == "fallback"


def test_router_finishes_when_answer_passes():
    state = {
        "answer_verification": {
            "passed": True
        },
        "generation_attempts": 1,
    }

    route = route_after_answer_verification(
        state
    )

    assert route == "finish"