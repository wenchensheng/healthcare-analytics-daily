#!/usr/bin/env python3
"""Generate the synthetic database, run every day's SQL, and execute notebooks."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.generate_synthetic import DB_PATH, generate
from shared.sqlutil import run_sql_file

DAYS = ROOT / "days"


def day_dirs() -> list[Path]:
    return sorted(
        p for p in DAYS.iterdir() if p.is_dir() and p.name.startswith("day-") and not p.name.startswith("_")
    )


def export_results(day: Path, results) -> None:
    out = day / "results"
    out.mkdir(exist_ok=True)
    for name, cols, rows in results:
        path = out / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(cols)
            writer.writerows(rows)


def execute_notebook(path: Path) -> None:
    import nbformat
    from nbclient import NotebookClient

    nb = nbformat.read(path, as_version=4)
    NotebookClient(
        nb,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(path.parent)}},
    ).execute()
    nbformat.write(nb, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-db", action="store_true", help="Regenerate the synthetic SQLite database.")
    parser.add_argument("--skip-notebooks", action="store_true", help="Only run SQL, do not execute notebooks.")
    args = parser.parse_args()

    if args.refresh_db or not DB_PATH.exists():
        print(f"Generating {DB_PATH} ...")
        counts = generate()
        for name, n in counts.items():
            print(f"  {name:28s} {n:>8,}")
    else:
        print(f"Using existing {DB_PATH} (pass --refresh-db to regenerate)")

    days = day_dirs()
    if not days:
        print("No day folders found under days/.")
        return 1

    for day in days:
        sql = day / "query.sql"
        if not sql.exists():
            print(f"SKIP {day.name}: no query.sql")
            continue
        print(f"SQL  {day.name}")
        results = run_sql_file(sql, DB_PATH)
        export_results(day, results)
        for name, cols, rows in results:
            print(f"     {name}: {len(rows)} rows")

        nb = day / "analysis.ipynb"
        if nb.exists() and not args.skip_notebooks:
            print(f"NB   {day.name}/analysis.ipynb")
            execute_notebook(nb)
            chart = day / "chart.png"
            print(f"     chart.png {'OK' if chart.exists() else 'MISSING'}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
