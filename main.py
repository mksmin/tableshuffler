import pandas as pd

from ai_analyzer import find_seating_groups
from pptx_inspector import (
    group_blocks_by_text,
    inspect_pptx,
    select_seating_blocks,
)
from pptx_writer import fill_seating_blocks
from validation import validate_seating_block

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
    print("\nДоступные листы:\n")

    for index, sheet_name in enumerate(
        sheet_names,
        start=1,
    ):
        print(f"{index}. {sheet_name}")

    while True:
        try:
            choice = int(
                input("\nВведите номер листа (числом): "),
            )

            if 1 <= choice <= len(sheet_names):
                return sheet_names[choice - 1]

            print("\nТакого листа нет")

        except ValueError:
            print("Введите номер листа числом")


def main() -> None:
    sheet_name = choose_sheet(INPUT_FILE)
    print("Вы выбрали лист:", sheet_name)

    df = pd.read_excel(
        INPUT_FILE,
        sheet_name=sheet_name,
    )

    if NAME_COLUMN not in df.columns:
        print(f"В документе нет столбца: {NAME_COLUMN}")
        print("Список столбцов:")
        print(list(df.columns))
        return

    listeners = df[[NAME_COLUMN]].dropna().copy()
    listeners[NAME_COLUMN] = listeners[NAME_COLUMN].astype(str).str.strip()

    listeners = listeners[listeners[NAME_COLUMN] != ""]
    print(f"\nНайдено слушателей: {len(listeners)}")

    if listeners.empty:
        print("В выбранном листе нет участников.")
        return

    while True:
        try:
            tables_count = int(
                input("Введите количество столов числом: "),
            )
            if tables_count <= 0:
                print("Количество столов должно быть больше 0.")
                continue

            if tables_count > len(listeners):
                print("Столов больше, чем слушателей.")
                continue

            break

        except ValueError:
            print("Введите количество столов числом")

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
        print(f"\nСтол {table_number}")

        for number, name in enumerate(
            table[NAME_COLUMN],
            start=1,
        ):
            print(f"{number}. {name}")

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

    print(f"\nГотово: {OUTPUT_FILE}")
    print(f"Презентация сохранена: {OUTPUT_PPTX}")
    print(
        "Количество строк:",
        len(result_rows),
    )


if __name__ == "__main__":
    main()
