import logging

import pandas as pd

from ai_analyzer import find_seating_groups
from pptx_inspector import (
    group_blocks_by_text,
    inspect_pptx,
    select_seating_blocks,
)
from pptx_writer import fill_seating_blocks
from validation import validate_seating_block

log = logging.getLogger(__name__)

INPUT_FILE = "footages/customers.xlsx"
OUTPUT_FILE = "footages/seating.xlsx"
NAME_COLUMN = "ФИО"

TEMPLATE_FILE = "footages/template.pptx"
OUTPUT_PPTX = "footages/result.pptx"


def choose_sheet(
    file_path: str,
) -> str:
    with pd.ExcelFile(file_path) as excel_file:
        sheet_names = [str(name) for name in excel_file.sheet_names]
    log.info("Доступные листы:")

    for index, sheet_name in enumerate(
        sheet_names,
        start=1,
    ):
        log.info("%s. %s", index, sheet_name)

    while True:
        try:
            choice = int(
                input("\nВведите номер листа (числом): "),
            )

            if 1 <= choice <= len(sheet_names):
                return sheet_names[choice - 1]

            log.info("Такого листа нет")

        except ValueError:
            log.info("Введите номер листа числом")


def main() -> None:
    sheet_name = choose_sheet(INPUT_FILE)
    log.info("Вы выбрали лист: %s", sheet_name)

    df = pd.read_excel(
        INPUT_FILE,
        sheet_name=sheet_name,
    )

    if NAME_COLUMN not in df.columns:
        log.info("В документе нет столбца: %s", NAME_COLUMN)
        log.info("Список столбцов: %s", list(df.columns))
        return

    listeners = df[[NAME_COLUMN]].dropna().copy()
    listeners[NAME_COLUMN] = listeners[NAME_COLUMN].astype(str).str.strip()

    listeners = listeners[listeners[NAME_COLUMN] != ""]
    log.info("Найдено слушателей: %s", len(listeners))

    if listeners.empty:
        log.info("В выбранном листе нет участников.")
        return

    while True:
        try:
            tables_count = int(
                input("Введите количество столов числом: "),
            )
            if tables_count <= 0:
                log.info("Количество столов должно быть больше 0.")
                continue

            if tables_count > len(listeners):
                log.info("Столов больше, чем слушателей.")
                continue

            break

        except ValueError:
            log.info("Введите количество столов числом")

    listeners = listeners.sample(
        frac=1,
    ).reset_index(
        drop=True,
    )

    listeners["Стол"] = [
        i % tables_count + 1
        for i in range(
            len(listeners),
        )
    ]

    result_rows = []
    tables: list[list[str]] = []

    for table_number in range(1, tables_count + 1):
        table = listeners[listeners["Стол"] == table_number].copy()

        table = table.sort_values(NAME_COLUMN)

        tables.append(
            table[NAME_COLUMN].tolist(),
        )
        log.info("Стол %s", table_number)

        for number, name in enumerate(
            table[NAME_COLUMN],
            start=1,
        ):
            log.info("%s. %s", number, name)

            result_rows.append(
                {
                    "Стол": table_number,
                    "№": number,
                    "ФИО": name,
                }
            )

    result = pd.DataFrame(result_rows)

    text_blocks = inspect_pptx(TEMPLATE_FILE)
    groups = group_blocks_by_text(text_blocks)
    seating_groups = find_seating_groups(groups)

    validated_blocks = validate_seating_block(
        seating_groups,
        len(tables),
    )
    selected_blocks = select_seating_blocks(
        text_blocks,
        validated_blocks,
    )[: len(tables)]

    fill_seating_blocks(
        template_path=TEMPLATE_FILE,
        output_path=OUTPUT_PPTX,
        selected_blocks=selected_blocks,
        tables=tables,
    )

    result.to_excel(
        OUTPUT_FILE,
        index=False,
    )

    log.info("Готово: %s", OUTPUT_FILE)
    log.info("Презентация сохранена: %s", OUTPUT_PPTX)
    log.info("Количество строк: %s", len(result_rows))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )
    main()
