from transformers import pipeline


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


print("[LLM] Loading shared Qwen model...")


generator = pipeline(
    "text-generation",
    model=MODEL_NAME,
    tokenizer=MODEL_NAME,
)


print("[LLM] Shared Qwen model ready.")


def generate_text(
    prompt: str,
    max_new_tokens: int = 120,
) -> str:
    messages = [
        {
            "role": "user",
            "content": prompt,
        }
    ]

    output = generator(
        messages,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        return_full_text=False,
    )

    generated = output[0][
        "generated_text"
    ]

    if isinstance(
        generated,
        list,
    ):
        generated = generated[-1][
            "content"
        ]

    return str(
        generated
    ).strip()