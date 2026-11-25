"""Shared synthetic data for the healthcare-analytics-daily series."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SHARED_DIR = Path(__file__).resolve().parent
DB_PATH = SHARED_DIR / "clinic.db"
SEED = 42

