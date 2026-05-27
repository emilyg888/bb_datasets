import csv
from pathlib import Path


BASE = Path(__file__).resolve().parent
DELTA_BASE = BASE / "delta_sources"
FULL_BASE = BASE / "full_sources"
FULL_DATES = ["2026-05-25", "2026-05-26", "2026-05-27", "2026-05-28"]


def read_rows(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def row_key_fields(rows):
    first_key = next(iter(rows[0]))
    return [first_key]


def apply_delta(rows, delta_rows):
    if not delta_rows:
        return rows
    fields = [field for field in delta_rows[0] if field != "delta_action"]
    keys = row_key_fields(rows)
    index = {tuple(row[key] for key in keys): i for i, row in enumerate(rows)}
    for delta in delta_rows:
        clean_delta = {field: delta[field] for field in fields}
        key = tuple(clean_delta[key] for key in keys)
        if delta.get("delta_action") == "UPDATE" and key in index:
            rows[index[key]] = clean_delta
    return rows


def main():
    table_paths = sorted(path for path in BASE.glob("*.csv") if path.is_file())
    current = {path.name: read_rows(path) for path in table_paths}
    fields_by_table = {name: list(rows[0].keys()) for name, rows in current.items()}

    for source_date in FULL_DATES:
        delta_manifest = read_rows(DELTA_BASE / source_date / "manifest.csv")
        changed_tables = {entry["table_name"] for entry in delta_manifest}
        for table_name in changed_tables:
            deltas = read_rows(DELTA_BASE / source_date / table_name)
            current[table_name] = apply_delta(current[table_name], deltas)

        manifest = []
        for table_name in sorted(current):
            write_rows(FULL_BASE / source_date / table_name, current[table_name], fields_by_table[table_name])
            manifest.append(
                {
                    "source_date": source_date,
                    "table_name": table_name,
                    "row_count": len(current[table_name]),
                    "extract_type": "synthetic_full_daily_extract",
                    "changed_from_previous_extract": "Y" if table_name in changed_tables else "N",
                }
            )

        write_rows(
            FULL_BASE / source_date / "manifest.csv",
            manifest,
            ["source_date", "table_name", "row_count", "extract_type", "changed_from_previous_extract"],
        )


if __name__ == "__main__":
    main()
