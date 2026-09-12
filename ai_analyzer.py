from pathlib import Path
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

PROMPT_PATH = Path(__file__).parent / "system_prompt.md"
system_prompt = PROMPT_PATH.read_text(
    encoding="utf-8",
)

client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio",
)


class Group(BaseModel):
    group_id: int
    text: str
    count: int
    shape_ids: list[int]


def classify_group(
    group: dict[str, Any],
) -> str:

    group_data = Group.model_validate(group).model_dump_json()

    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": group_data,
        },
    ]
    model_settings = {
        "model": "qwen3-8b",
        "messages": messages,
        "temperature": 0,
        "max_tokens": 100,
        "extra_body": {
            "chat_template_kwargs": {
                "enable_thinking": False,
            },
        },
    }

    response = client.chat.completions.create(
        **model_settings,
    )

    content = response.choices[0].message.content

    if not content or not content.strip():
        finish_reason = response.choices[0].finish_reason
        raise RuntimeError(
            f"Модель вернула пустой ответ. finish_reason: {finish_reason}",
        )

    role = content.strip().lower()

    if role not in {
        "seating",
        "other",
    }:
        raise RuntimeError(
            f"Неизвестный ответ модели: {role!r}",
        )

    return role


def find_seating_groups(
    groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = []
    for group in groups:
        role = classify_group(group)

        print(
            f"Group {group.get("group_id")} | "
            f"count={group.get('count')} | "
            f"text={group.get('text')} | "
            f"-> {role}",
        )

        if role == "seating":
            result.append(group)

    return result
