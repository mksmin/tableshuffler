from typing import Any

from pptx import Presentation

from ai_analyzer import find_seating_groups
from ai_analyzer import group_blocks_by_text


def inspect_pptx(
    pptx_path: str,
) -> list[dict[str, Any]]:
    prs = Presentation(pptx_path)

    slide_width = prs.slide_width
    slide_height = prs.slide_height

    text_blocks = []

    for slide_number, slide in enumerate(
        prs.slides,
        start=1,
    ):

        for shape in slide.shapes:
            if not shape.has_text_frame:
                continue

            text_blocks.append(
                {
                    "slide": slide_number,
                    "shape_id": shape.shape_id,
                    "name": shape.name,
                    "text": shape.text.strip(),
                    "x": round(shape.left / slide_width * 100, 1),
                    "y": round(shape.top / slide_height * 100, 1),
                    "width": round(shape.width / slide_width * 100, 1),
                    "height": round(shape.height / slide_height * 100, 1),
                }
            )

    return text_blocks


if __name__ == "__main__":
    pptx_path = "./footages/template.pptx"

    text_bl = inspect_pptx(pptx_path)
    print("Блоки:")

    for block in text_bl:
        print(block)

    # seating_blocks = find_seating_blocks(text_bl)
    # print()
    # print("Блоки рассадки:")
    #
    # for block in seating_blocks:
    #     print(block)

    groups = group_blocks_by_text(text_bl)

    print("\nГруппы:")

    for group in groups:
        print(
            f"group={group['group_id']} | "
            f"count={group['count']} | "
            f"text={group['text']!r} | "
            f"shape_ids={group['shape_ids']} | "
            f"avg_width={group['avg_width']} | "
            f"avg_height={group['avg_height']}"
        )

    seating_groups = find_seating_groups(groups)

    print("\nГруппы рассадки:")

    for group in seating_groups:
        print(
            f"group={group['group_id']} | "
            f"count={group['count']} | "
            f"shape_ids={group['shape_ids']}"
        )
