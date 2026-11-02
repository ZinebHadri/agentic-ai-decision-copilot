import re
from typing import Any


def collect_numeric_values(
    data: Any
) -> list[float]:
    values = []

    if isinstance(data, dict):
        for value in data.values():
            values.extend(
                collect_numeric_values(value)
            )

    elif isinstance(data, list):
        for item in data:
            values.extend(
                collect_numeric_values(item)
            )

    elif isinstance(data, (int, float)):
        values.append(float(data))

    return values


def collect_text_values(
    data: Any
) -> list[str]:
    values = []

    if isinstance(data, dict):
        for value in data.values():
            values.extend(
                collect_text_values(value)
            )

    elif isinstance(data, list):
        for item in data:
            values.extend(
                collect_text_values(item)
            )

    elif isinstance(data, str):
        values.append(data)

    return values


def extract_answer_numbers(
    answer: str
) -> list[float]:
    matches = re.findall(
        r"(?<!\w)[+-]?\$?\d[\d,]*(?:\.\d+)?",
        answer,
    )

    numbers = []

    for match in matches:
        cleaned = (
            match
            .replace("$", "")
            .replace(",", "")
        )

        try:
            numbers.append(
                float(cleaned)
            )
        except ValueError:
            continue

    return numbers


def number_is_grounded(
    number: float,
    allowed_values: list[float],
    tolerance: float = 0.01,
) -> bool:
    for allowed in allowed_values:
        if abs(number - allowed) <= tolerance:
            return True

    return False


def number_appears_in_text(
    number: float,
    text_values: list[str],
) -> bool:
    integer_form = str(
        int(number)
    )

    decimal_form = str(
        number
    )

    for text in text_values:
        if integer_form in text:
            return True

        if decimal_form in text:
            return True

    return False


def verify_answer_numbers(
    answer: str,
    tool_result: dict,
) -> dict:
    answer_numbers = extract_answer_numbers(
        answer
    )

    allowed_values = collect_numeric_values(
        tool_result
    )

    text_values = collect_text_values(
        tool_result
    )

    unsupported_numbers = []

    for number in answer_numbers:
        if number_is_grounded(
            number,
            allowed_values,
        ):
            continue

        if number_appears_in_text(
            number,
            text_values,
        ):
            continue

        unsupported_numbers.append(
            number
        )

    passed = (
        len(unsupported_numbers) == 0
    )

    return {
        "passed": passed,
        "answer_numbers": answer_numbers,
        "unsupported_numbers": unsupported_numbers,
    }