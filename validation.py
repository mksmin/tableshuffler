from typing import Any


def validate_seating_block(
    seating_groups: list[dict[str, Any]],
    required_seats: int,
):
    seating_block = [block for group in seating_groups for block in group["blocks"]]

    found_blocks = len(seating_block)

    if found_blocks < required_seats:
        raise ValueError(
            "Количество блоков рассадки недостаточно. \n\n"
            f"Необходимо: {required_seats}\n"
            f"Найдено: {found_blocks}\n"
            f"Генерация остановлена"
        )

    return seating_block
