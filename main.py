import pandas as pd

INPUT_FILE = "КАДРЫ Заявки.xlsx"
OUTPUT_FILE = "seating.xlsx"
NAME_COLUMN = "ФИО"


def choose_sheet(
    file_path: str,
) -> str:
    excel_file = pd.ExcelFile(file_path)
    print("\nДоступные листы:\n")

    for index, sheet_name in enumerate(
        excel_file.sheet_names,
        start=1,
    ):
        print(f"{index}. {sheet_name}")

    while True:
        try:
            choice = int(
                input("\nВведите номер листа (числом): "),
            )

            if 1 <= choice <= len(excel_file.sheet_names):
                return excel_file.sheet_names[choice - 1]

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
            print("Введите количество строк числом")

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

    for table_number in range(1, tables_count + 1):
        table = listeners[listeners["Стол"] == table_number].copy()

        table = table.sort_values(NAME_COLUMN)

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

    result.to_excel(
        OUTPUT_FILE,
        index=False,
    )

    print(f"\nГотово: {OUTPUT_FILE}")
    print(
        "Количество строк:",
        len(result_rows),
    )


if __name__ == "__main__":
    main()
