from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from src.agentic.nodes import (
    create_plan,
    decide_next_step,
    execute_next_tool,
    execute_tool,
    generate_answer,
    generate_safe_fallback,
    route_after_answer_verification,
    route_query,
    verify_answer,
    verify_result,
)
from src.agentic.state import (
    AgentState,
    create_initial_state,
)


def choose_execution_mode(
    state: AgentState,
) -> str:
    plan = state.get(
        "plan",
        [],
    )

    if len(plan) == 0:
        print(
            "[GRAPH] No executable plan."
        )
        return "failure"

    if len(plan) == 1:
        print(
            "[GRAPH] Single-step execution."
        )
        return "single"

    print(
        "[GRAPH] Multi-step execution."
    )

    return "multi"


def route_after_tool_verification(
    state: AgentState,
) -> str:
    if state.get(
        "verification_passed",
        False,
    ):
        return "generate"

    return "failure"


def failure_node(
    state: AgentState,
) -> AgentState:
    state[
        "final_answer"
    ] = (
        "The requested analysis could not "
        "be completed with a valid analytics result."
    )

    state[
        "answer_verification"
    ] = {
        "passed": False,
        "source": "system_failure",
        "numeric": {
            "passed": False,
            "unsupported_numbers": [],
        },
        "quality": {
            "passed": False,
            "missing_requirements": [],
        },
    }

    print(
        "[GRAPH] Analysis failed."
    )

    return state


def build_agentic_graph(
    df_sales,
    df_raw,
):
    graph = StateGraph(
        AgentState
    )

    def execute_single_tool_node(
        state: AgentState,
    ) -> AgentState:
        updated_state = execute_tool(
            state=state,
            df_sales=df_sales,
            df_raw=df_raw,
        )

        print(
            "[SINGLE-STEP] Tool results keys:",
            list(
                updated_state.get(
                    "tool_results",
                    {},
                ).keys()
            ),
        )

        return updated_state

    def execute_next_tool_node(
        state: AgentState,
    ) -> AgentState:
        updated_state = execute_next_tool(
            state=state,
            df_sales=df_sales,
            df_raw=df_raw,
        )

        print(
            "[MULTI-STEP] Tool results keys:",
            list(
                updated_state.get(
                    "tool_results",
                    {},
                ).keys()
            ),
        )

        return updated_state

    graph.add_node(
        "route_query",
        route_query,
    )

    graph.add_node(
        "create_plan",
        create_plan,
    )

    graph.add_node(
        "execute_single_tool",
        execute_single_tool_node,
    )

    graph.add_node(
        "execute_next_tool",
        execute_next_tool_node,
    )

    graph.add_node(
        "verify_result",
        verify_result,
    )

    graph.add_node(
        "generate_answer",
        generate_answer,
    )

    graph.add_node(
        "verify_answer",
        verify_answer,
    )

    graph.add_node(
        "safe_fallback",
        generate_safe_fallback,
    )

    graph.add_node(
        "failure",
        failure_node,
    )

    graph.add_edge(
        START,
        "route_query",
    )

    graph.add_edge(
        "route_query",
        "create_plan",
    )

    graph.add_conditional_edges(
        "create_plan",
        choose_execution_mode,
        {
            "single": "execute_single_tool",
            "multi": "execute_next_tool",
            "failure": "failure",
        },
    )

    graph.add_edge(
        "execute_single_tool",
        "verify_result",
    )

    graph.add_conditional_edges(
        "execute_next_tool",
        decide_next_step,
        {
            "continue": "execute_next_tool",
            "verify": "verify_result",
        },
    )

    graph.add_conditional_edges(
        "verify_result",
        route_after_tool_verification,
        {
            "generate": "generate_answer",
            "failure": "failure",
        },
    )

    graph.add_edge(
        "generate_answer",
        "verify_answer",
    )

    graph.add_conditional_edges(
        "verify_answer",
        route_after_answer_verification,
        {
            "finish": END,
            "fallback": "safe_fallback",
        },
    )

    graph.add_edge(
        "safe_fallback",
        END,
    )

    graph.add_edge(
        "failure",
        END,
    )

    return graph.compile()


def run_agentic_copilot(
    question: str,
    df_sales,
    df_raw,
):
    initial_state = (
        create_initial_state(
            question
        )
    )

    graph = build_agentic_graph(
        df_sales=df_sales,
        df_raw=df_raw,
    )

    final_state = graph.invoke(
        initial_state
    )

    return final_state