from pathlib import Path
from typing import Any

from pptx import Presentation


def fill_seating_blocks(
    template_path: Path | str,
    output_path: Path | str,
    selected_blocks: list[dict[str, Any]],
    tables: list[list[str]],
) -> None:

    if len(selected_blocks) < len(tables):
        raise ValueError(
            "Недостаточно блоков для вставки рассадки",
        )

    prs = Presentation(
        str(template_path),
    )

    for table_number, (block, names) in enumerate(
        zip(
            selected_blocks,
            tables,
        ),
        start=1,
    ):
        slide = prs.slides[block["slide"] - 1]

        shape = next(
            (shape for shape in slide.shapes if shape.shape_id == block["shape_id"]),
            None,
        )

        if shape is None:
            raise ValueError(
                f"Shape не найден: "
                f"slide={block['slide']}, "
                f"shape_id={block['shape_id']}"
            )

        if not shape.has_text_frame:
            raise ValueError(
                f"Shape не содержит текст: " f"shape_id={block['shape_id']}"
            )

        shape.text = "\n".join(
            [
                f"Стол {table_number}",
                "",
                *names,
            ]
        )

    output = Path(output_path) if isinstance(output_path, str) else output_path
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    prs.save(
        str(output),
    )
