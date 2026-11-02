import json

from src.llm.shared_model import generate_text


def build_answer_prompt(
    question: str,
    tool_result: dict,
) -> str:
    data = json.dumps(
        tool_result,
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    return f"""
You are a business analytics assistant.

Answer the user's question using ONLY the verified
analytics results provided below.

STRICT RULES:

- Never invent numbers.
- Never estimate numbers.
- Never calculate new percentages.
- Copy numerical values exactly from the analytics results.
- Do not change decimal placement.
- Do not claim causation unless the data proves it.
- If several analytics tools were used, answer every part
  of the user's question.
- Be concise and business-focused.
- Mention the key evidence, not every field.
- Do not add unsupported recommendations.

User question:
{question}

Verified analytics results:
{data}

Write the final business answer.
""".strip()


def generate_business_answer(
    question: str,
    tool_result: dict,
) -> str:
    prompt = build_answer_prompt(
        question=question,
        tool_result=tool_result,
    )

    return generate_text(
        prompt=prompt,
        max_new_tokens=220,
    )