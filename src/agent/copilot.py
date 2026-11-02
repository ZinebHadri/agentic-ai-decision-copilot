from src.agent.executor import execute_business_query
from src.agent.answer_generator import generate_business_answer


def ask_business_copilot(
    question: str,
    df_sales,
    df_raw,
) -> dict:
    analysis = execute_business_query(
        question=question,
        df_sales=df_sales,
        df_raw=df_raw,
    )

    if "error" in analysis:
        return {
            "question": question,
            "answer": analysis["error"],
            "analysis": analysis,
        }

    answer = generate_business_answer(
        question=question,
        tool_result=analysis,
    )

    return {
        "question": question,
        "answer": answer,
        "analysis": analysis,
    }