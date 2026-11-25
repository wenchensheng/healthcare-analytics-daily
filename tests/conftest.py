from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.generate_synthetic import DB_PATH, generate  # noqa: E402


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def db_path() -> Path:
    if not DB_PATH.exists():
        generate()
    return DB_PATH


@pytest.fixture(scope="session")
def day_dirs(repo_root: Path) -> list[Path]:
    days = repo_root / "days"
    return sorted(
        p for p in days.iterdir() if p.is_dir() and p.name.startswith("day-") and not p.name.startswith("_")
    )
