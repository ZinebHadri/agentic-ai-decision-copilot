from typing import TypedDict, Any


class AgentState(TypedDict):
    question: str

    intent: str
    month: str | None
    previous_month: str | None

    plan: list[str]
    current_step: int
    completed_tools: list[str]

    tool_result: dict[str, Any]
    tool_results: dict[str, Any]

    needs_more_analysis: bool
    verification_passed: bool

    draft_answer: str
    answer_verification: dict[str, Any]
    generation_attempts: int

    final_answer: str


def create_initial_state(
    question: str
) -> AgentState:
    return {
        "question": question,

        "intent": "",
        "month": None,
        "previous_month": None,

        "plan": [],
        "current_step": 0,
        "completed_tools": [],

        "tool_result": {},
        "tool_results": {},

        "needs_more_analysis": False,
        "verification_passed": False,

        "draft_answer": "",
        "answer_verification": {},
        "generation_attempts": 0,

        "final_answer": "",
    }