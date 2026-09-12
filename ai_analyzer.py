import json
from collections import defaultdict
from typing import Any

from openai import OpenAI


def group_blocks_by_text(
    text_blocks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for block in text_blocks:
        key = block["text"].strip().lower()
        groups[key].append(block)

    result = []

    for group_id, (text, blocks) in enumerate(
        groups.items(),
        start=1,
    ):
        result.append(
            {
                "group_id": group_id,
                "text": text,
                "count": len(blocks),
                "shape_ids": [block["shape_id"] for block in blocks],
                "avg_width": round(
                    sum(block["width"] for block in blocks) / len(blocks),
                    1,
                ),
                "avg_height": round(
                    sum(block["height"] for block in blocks) / len(blocks),
                    1,
                ),
                "blocks": blocks,
            }
        )

    return result


client = OpenAI(
    base_url="http://127.0.0.1:1234/v1",
    api_key="lm-studio",
)


SYSTEM_PROMPT = """
Ты анализируешь группы текстовых объектов PowerPoint-шаблона.

Нужно определить назначение ОДНОЙ группы.

Допустимые ответы:

seating — группа текстовых блоков, предназначенных для размещения
списков ФИО участников по столам.

other — всё остальное:
заголовки, даты, комментарии, подписи, расписание,
описания и служебный текст.

Признаки seating:
- блоки повторяются;
- имеют одинаковый или очень похожий текст;
- располагаются как серия одинаковых элементов;
- текст может быть шаблонным, например "СТОЛ\\nФИО";
- каждый такой блок предполагается заполнить участниками отдельного стола.

Ответь ТОЛЬКО одним словом:

seating

или

other
"""


def classify_group(
    group: dict[str, Any],
) -> str:
    # Сам список blocks модели пока не нужен целиком.
    # Оставляем только полезное описание группы.
    group_data = {
        "group_id": group["group_id"],
        "text": group["text"],
        "count": group["count"],
        "shape_ids": group["shape_ids"],
        "avg_width": group["avg_width"],
        "avg_height": group["avg_height"],
    }

    group_json = json.dumps(
        group_data,
        ensure_ascii=False,
        indent=2,
    )

    response = client.chat.completions.create(
        model="qwen",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": group_json,
            },
        ],
        temperature=0,
        max_tokens=32,
        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": False,
            }
        },
    )

    content = response.choices[0].message.content

    if not content or not content.strip():
        finish_reason = response.choices[0].finish_reason
        raise RuntimeError(
            f"Модель вернула пустой ответ. finish_reason={finish_reason!r}"
        )

    role = content.strip().lower()

    if role not in {"seating", "other"}:
        raise RuntimeError(f"Неизвестный ответ модели: {role!r}")

    return role


def find_seating_groups(
    groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    result = []

    for group in groups:
        role = classify_group(group)

        print(
            f"Group {group['group_id']} | "
            f"count={group['count']} | "
            f"text={group['text']!r} "
            f"-> {role}"
        )

        if role == "seating":
            result.append(group)

    return result
