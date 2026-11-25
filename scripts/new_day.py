#!/usr/bin/env python3
"""Create the next day folder from days/_template.

Usage:
    python scripts/new_day.py monthly-denial-rate --title "Monthly claim denial rate by payer"
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DAYS = ROOT / "days"
TEMPLATE = DAYS / "_template"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def next_day_number() -> int:
    nums = []
    for p in DAYS.iterdir():
        m = re.match(r"day-(\d+)-", p.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) if nums else 0) + 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug", help="kebab-case folder slug, without the day-NNN- prefix")
    parser.add_argument("--title", default="", help="Human title to drop into the day README")
    args = parser.parse_args()

    slug = args.slug.strip().lower()
    if slug.startswith("day-"):
        sys.exit("Pass only the slug, e.g. monthly-denial-rate, not day-002-...")
    if not SLUG_RE.match(slug):
        sys.exit("Slug must be kebab-case: lowercase letters, numbers, and hyphens.")
    if not TEMPLATE.exists():
        sys.exit(f"Template folder missing: {TEMPLATE}")

    n = next_day_number()
    name = f"day-{n:03d}-{slug}"
    dest = DAYS / name
    if dest.exists():
        sys.exit(f"Already exists: {dest}")

    shutil.copytree(TEMPLATE, dest)
    readme = dest / "README.md"
    if readme.exists():
        text = readme.read_text(encoding="utf-8")
        text = text.replace("DAY_NUMBER", f"{n:03d}")
        text = text.replace("DAY_TITLE", args.title or slug.replace("-", " ").title())
        text = text.replace("DAY_SLUG", name)
        readme.write_text(text, encoding="utf-8")

    print(f"Created {dest.relative_to(ROOT)}")
    print("Next:")
    print("  1. Write query.sql with /* name: ... */ blocks.")
    print("  2. Edit analysis.ipynb so it answers the business question and saves chart.png.")
    print("  3. python run_all.py")
    print("  4. Fill in this day's README.md with the actual numbers from results/.")
    print("  5. Add a row to the index table in README.md and check off BACKLOG.md.")
    print("  6. pytest")
    print("  7. Commit locally. Do not push until you are ready to publish the new day.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
