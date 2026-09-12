from typing import Any

from pptx import Presentation

from ai_analyzer import find_seating_groups
from ai_analyzer import group_blocks_by_text
from validation import validate_seating_block


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
    pptx_path = "./footages/Template.pptx"

    text_bl = inspect_pptx(pptx_path)
    groups = group_blocks_by_text(text_bl)
    seating_groups = find_seating_groups(groups)

    required_tables = 6
    seating_blocks = validate_seating_block(
        seating_groups,
        required_tables,
    )

    print(
        f"\nВалидация пройдена: "
        f"требуется {required_tables}, "
        f"доступно {len(seating_blocks)}"
    )
