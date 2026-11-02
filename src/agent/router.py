import json
import re

from transformers import AutoModelForCausalLM, AutoTokenizer

from src.agent.schemas import QueryIntent


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

_tokenizer = None
_model = None


def get_model():
    global _tokenizer
    global _model

    if _tokenizer is None:
        _tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME
        )

    if _model is None:
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME
        )

    return _tokenizer, _model


def build_prompt(question: str) -> str:
    return f"""
You are a routing agent for a business analytics system.

Classify the user's question into exactly one intent.

Allowed intents:

revenue_change
Use when the user asks why revenue changed between two periods.

business_performance
Use when the user asks about performance, overview, KPIs,
top products, top customers, top countries, sales or revenue
for one period.

returns_analysis
Use when the user asks about returns, cancellations or refunds.

unknown
Use when none of the other intents apply.

Extract months when possible.

Use YYYY-MM format.

Return exactly one JSON object with these fields:

intent
month
previous_month

Examples:

Question:
How did September 2011 perform?

Output:
{{
  "intent": "business_performance",
  "month": "2011-09",
  "previous_month": null
}}

Question:
Why did revenue fall from March 2011 to April 2011?

Output:
{{
  "intent": "revenue_change",
  "month": "2011-04",
  "previous_month": "2011-03"
}}

Question:
Which products had the most returns in April 2011?

Output:
{{
  "intent": "returns_analysis",
  "month": "2011-04",
  "previous_month": null
}}

Question:
{question}

Do not explain.
Do not use markdown.
Return only JSON.
""".strip()


def generate_router_output(
    question: str
) -> str:
    tokenizer, model = get_model()

    prompt = build_prompt(question)

    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        formatted_prompt,
        return_tensors="pt",
    )

    output_ids = model.generate(
        **inputs,
        max_new_tokens=100,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )

    generated_ids = output_ids[
        0,
        inputs["input_ids"].shape[1]:
    ]

    output = tokenizer.decode(
        generated_ids,
        skip_special_tokens=True,
    )

    return output.strip()


def extract_json_object(
    raw_output: str
) -> str:
    cleaned = raw_output.strip()

    cleaned = cleaned.replace(
        "```json",
        ""
    )

    cleaned = cleaned.replace(
        "```",
        ""
    )

    match = re.search(
        r"\{.*\}",
        cleaned,
        re.DOTALL,
    )

    if not match:
        raise ValueError(
            f"No JSON object found in model output: {raw_output!r}"
        )

    return match.group(0)


def parse_router_output(
    raw_output: str
) -> QueryIntent:
    json_text = extract_json_object(
        raw_output
    )

    data = json.loads(
        json_text
    )

    return QueryIntent(
        **data
    )


def route_question(
    question: str
) -> QueryIntent:
    raw_output = generate_router_output(
        question
    )

    print(
        "[LLM ROUTER RAW OUTPUT]",
        raw_output
    )

    return parse_router_output(
        raw_output
    )