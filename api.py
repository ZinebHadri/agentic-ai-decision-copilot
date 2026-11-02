from pathlib import Path
from typing import Any
import re

import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agentic.graph import run_agentic_copilot


BASE_DIR = Path(__file__).resolve().parent

DATA_PATH = (
    BASE_DIR
    / "data"
    / "Online Retail.xlsx"
)


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATA_PATH}"
        )

    df_raw = pd.read_excel(
        DATA_PATH
    )

    df_sales = df_raw[
        (df_raw["Quantity"] > 0)
        & (df_raw["UnitPrice"] > 0)
        & (
            ~df_raw["InvoiceNo"]
            .astype(str)
            .str.startswith("C")
        )
    ].copy()

    df_sales = (
        df_sales
        .drop_duplicates()
        .copy()
    )

    df_sales["Revenue"] = (
        df_sales["Quantity"]
        * df_sales["UnitPrice"]
    )

    df_sales["Month"] = (
        df_sales["InvoiceDate"]
        .dt
        .to_period("M")
        .astype(str)
    )

    return (
        df_raw,
        df_sales,
    )


print("[API] Loading dataset...")

DF_RAW, DF_SALES = load_data()

print("[API] Dataset loaded.")
print("[API] Raw rows:", len(DF_RAW))
print(
    "[API] Valid sales rows:",
    len(DF_SALES),
)


app = FastAPI(
    title="Agentic AI Decision Copilot API",
    description=(
        "Agentic analytics API using "
        "Qwen, LangGraph, deterministic "
        "analytics tools and verification."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


class HealthResponse(BaseModel):
    status: str
    raw_rows: int
    sales_rows: int


class AskResponse(BaseModel):
    question: str
    final_answer: str
    plan: list[str]
    completed_tools: list[str]
    verification: dict[str, Any]
    generation_attempts: int
    used_fallback: bool
    needs_clarification: bool
    clarification: dict[str, Any]
    tool_results: dict[str, Any]


MONTH_NAMES = (
    "january|february|march|april|may|june|"
    "july|august|september|october|november|december"
)

MONTH_PATTERN = re.compile(
    rf"\b(?:{MONTH_NAMES})\s+\d{{4}}\b"
    rf"|\b\d{{4}}[-/]\d{{1,2}}\b",
    flags=re.IGNORECASE,
)


def extract_period_mentions(
    question: str,
):
    return MONTH_PATTERN.findall(
        question
    )


def looks_like_customer_contribution(
    question: str,
):
    q = question.lower()

    customer_words = (
        "customer",
        "customers",
        "client",
        "clients",
    )

    contribution_words = (
        "contributed",
        "contribute",
        "contribution",
        "decline",
        "drop",
        "fall",
        "decrease",
        "change",
        "impact",
        "responsible",
    )

    has_customer = any(
        word in q
        for word in customer_words
    )

    has_contribution = any(
        word in q
        for word in contribution_words
    )

    return (
        has_customer
        and has_contribution
    )


def looks_like_revenue_comparison(
    question: str,
):
    q = question.lower()

    revenue_words = (
        "revenue",
        "sales",
        "turnover",
    )

    comparison_words = (
        "fall",
        "fell",
        "decline",
        "drop",
        "decrease",
        "increase",
        "change",
        "compare",
        "comparison",
        "difference",
        "grew",
        "growth",
    )

    has_revenue = any(
        word in q
        for word in revenue_words
    )

    has_comparison = any(
        word in q
        for word in comparison_words
    )

    return (
        has_revenue
        and has_comparison
    )


def looks_like_returns_question(
    question: str,
):
    q = question.lower()

    keywords = (
        "return",
        "returns",
        "returned",
        "refund",
        "refunds",
    )

    return any(
        word in q
        for word in keywords
    )


def looks_like_anomaly_question(
    question: str,
):
    q = question.lower()

    keywords = (
        "unusual",
        "unusually",
        "anomaly",
        "anomalous",
        "abnormal",
        "weak",
        "strong",
        "outlier",
    )

    return any(
        word in q
        for word in keywords
    )


def looks_like_performance_question(
    question: str,
):
    q = question.lower()

    keywords = (
        "perform",
        "performed",
        "performance",
        "how did",
        "kpi",
        "kpis",
    )

    return any(
        word in q
        for word in keywords
    )


def clarification_response(
    question: str,
    clarification_type: str,
):
    if clarification_type == "two_periods":
        return {
            "question": question,
            "final_answer": (
                "I can analyze that, but I need "
                "two periods to compare."
            ),
            "plan": [],
            "completed_tools": [],
            "verification": {
                "passed": False,
                "source": "needs_context",
            },
            "generation_attempts": 0,
            "used_fallback": False,
            "needs_clarification": True,
            "clarification": {
                "title": (
                    "Two periods are needed"
                ),
                "message": (
                    "Please specify the start month "
                    "and the end month you want "
                    "to compare."
                ),
                "required_fields": [
                    "Start month",
                    "End month",
                ],
                "examples": [
                    (
                        "Which customers contributed "
                        "most to the revenue decline "
                        "from March 2011 "
                        "to April 2011?"
                    ),
                    (
                        "Why did revenue change "
                        "from August 2011 "
                        "to September 2011?"
                    ),
                ],
            },
            "tool_results": {},
        }

    if clarification_type == "one_period":
        return {
            "question": question,
            "final_answer": (
                "I can analyze that, but I need "
                "the month you want me to evaluate."
            ),
            "plan": [],
            "completed_tools": [],
            "verification": {
                "passed": False,
                "source": "needs_context",
            },
            "generation_attempts": 0,
            "used_fallback": False,
            "needs_clarification": True,
            "clarification": {
                "title": (
                    "A month is needed"
                ),
                "message": (
                    "Please specify the month "
                    "you want to analyze."
                ),
                "required_fields": [
                    "Month",
                ],
                "examples": [
                    (
                        "How did September 2011 "
                        "perform?"
                    ),
                    (
                        "Was April 2011 "
                        "unusually weak?"
                    ),
                    (
                        "What were the returns "
                        "in April 2011?"
                    ),
                ],
            },
            "tool_results": {},
        }

    return {
        "question": question,
        "final_answer": (
            "I need a little more information "
            "before I can run the analysis."
        ),
        "plan": [],
        "completed_tools": [],
        "verification": {
            "passed": False,
            "source": "needs_context",
        },
        "generation_attempts": 0,
        "used_fallback": False,
        "needs_clarification": True,
        "clarification": {
            "title": (
                "More information needed"
            ),
            "message": (
                "Please include the month "
                "or comparison period "
                "you want to analyze."
            ),
            "required_fields": [],
            "examples": [
                (
                    "How did September 2011 "
                    "perform?"
                ),
                (
                    "Why did revenue fall "
                    "from March 2011 "
                    "to April 2011?"
                ),
            ],
        },
        "tool_results": {},
    }


def precheck_question(
    question: str,
):
    periods = extract_period_mentions(
        question
    )

    period_count = len(
        periods
    )

    if looks_like_customer_contribution(
        question
    ):
        if period_count < 2:
            return clarification_response(
                question=question,
                clarification_type="two_periods",
            )

    if looks_like_revenue_comparison(
        question
    ):
        if period_count < 2:
            return clarification_response(
                question=question,
                clarification_type="two_periods",
            )

    if looks_like_returns_question(
        question
    ):
        if period_count < 1:
            return clarification_response(
                question=question,
                clarification_type="one_period",
            )

    if looks_like_anomaly_question(
        question
    ):
        if period_count < 1:
            return clarification_response(
                question=question,
                clarification_type="one_period",
            )

    if looks_like_performance_question(
        question
    ):
        if period_count < 1:
            return clarification_response(
                question=question,
                clarification_type="one_period",
            )

    return None


def classify_missing_context(
    error: Exception,
):
    message = str(
        error
    ).lower()

    if (
        "customer_contribution"
        in message
        or "revenue_change"
        in message
        or (
            "previous_month"
            in message
            and "month"
            in message
        )
    ):
        return "two_periods"

    if (
        "business_performance"
        in message
        or "returns_analysis"
        in message
        or "anomaly_analysis"
        in message
        or "requires month"
        in message
    ):
        return "one_period"

    return None


@app.get("/")
def root():
    return {
        "name": (
            "Agentic AI "
            "Decision Copilot"
        ),
        "status": "running",
        "endpoints": {
            "health": "/health",
            "ask": "/ask",
            "docs": "/docs",
        },
    }


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health():
    return {
        "status": "healthy",
        "raw_rows": len(
            DF_RAW
        ),
        "sales_rows": len(
            DF_SALES
        ),
    }


@app.post(
    "/ask",
    response_model=AskResponse,
)
def ask(
    request: QuestionRequest,
):
    question = (
        request.question.strip()
    )

    if not question:
        raise HTTPException(
            status_code=400,
            detail=(
                "Question cannot be empty."
            ),
        )

    fast_response = precheck_question(
        question
    )

    if fast_response is not None:
        return fast_response

    try:
        final_state = (
            run_agentic_copilot(
                question=question,
                df_sales=DF_SALES,
                df_raw=DF_RAW,
            )
        )

    except ValueError as error:
        context_type = (
            classify_missing_context(
                error
            )
        )

        if context_type:
            return clarification_response(
                question=question,
                clarification_type=context_type,
            )

        return clarification_response(
            question=question,
            clarification_type="general",
        )

    except Exception as error:
        print(
            "[API ERROR]",
            repr(error),
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "The agent could not "
                "complete the analysis."
            ),
        ) from error

    verification = (
        final_state.get(
            "answer_verification",
            {},
        )
    )

    used_fallback = (
        verification.get(
            "source"
        )
        == "safe_fallback"
    )

    return {
        "question": question,
        "final_answer": (
            final_state.get(
                "final_answer",
                "",
            )
        ),
        "plan": (
            final_state.get(
                "plan",
                [],
            )
        ),
        "completed_tools": (
            final_state.get(
                "completed_tools",
                [],
            )
        ),
        "verification": verification,
        "generation_attempts": (
            final_state.get(
                "generation_attempts",
                0,
            )
        ),
        "used_fallback": used_fallback,
        "needs_clarification": False,
        "clarification": {},
        "tool_results": (
            final_state.get(
                "tool_results",
                {},
            )
        ),
    }