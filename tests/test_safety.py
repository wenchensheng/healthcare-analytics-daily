"""Guards against employer data, real Epic schema names, and PHI-like content."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

TEXT_SUFFIXES = {".md", ".py", ".sql", ".csv", ".txt", ".yml", ".yaml", ".json", ".ipynb", ".toml"}
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ipynb_checkpoints"}

# Employer / real-system names that must never appear in this portfolio series.
FORBIDDEN_PHRASES = [
    re.compile(r"northwell", re.I),
    re.compile(r"north\s*shore[- ]?lij", re.I),
    re.compile(r"feinstein", re.I),
    re.compile(r"lenox\s*hill", re.I),
    re.compile(r"cohen\s*children", re.I),
    re.compile(r"peconic\s*bay", re.I),
]

# Real Epic reporting-table style names. Mentions of Epic, Clarity, Caboodle,
# or Willow in a bio or disclaimer are allowed.
EPIC_SCHEMA_NAMES = [
    re.compile(r"\bPAT_ENC(_HSP)?\b"),
    re.compile(r"\bCLARITY_DEP\b"),
    re.compile(r"\bCLARITY_MEDICATION\b"),
    re.compile(r"\bF_SCHED_APPT\b"),
    re.compile(r"\bORDER_MED\b"),
    re.compile(r"\bHSP_ACCOUNT\b"),
    re.compile(r"\bORDER_PROC\b"),
    re.compile(r"\bIP_FLWSHT(_MEAS)?\b"),
    re.compile(r"\bF_IP_HSP_ADMISSION\b"),
    re.compile(r"\bPatientDim\b"),
    re.compile(r"\bEncounterFact\b"),
]

SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# US-style phone numbers, not dates or identifiers like P000001.
PHONE_RE = re.compile(r"\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s])\d{3}[-.\s]\d{4}\b")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b", re.I)


def _iter_text_files(repo_root: Path):
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        # This file itself lists the forbidden patterns.
        if path.name == "test_safety.py":
            continue
        yield path


@pytest.fixture(scope="module")
def text_files(repo_root: Path) -> list[tuple[Path, str]]:
    files = []
    for path in _iter_text_files(repo_root):
        try:
            files.append((path, path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue
    return files


def test_no_employer_or_forbidden_names(repo_root: Path, text_files) -> None:
    hits = []
    for path, text in text_files:
        for pat in FORBIDDEN_PHRASES:
            for m in pat.finditer(text):
                hits.append(f"{path.relative_to(repo_root)}: {m.group(0)!r}")
    assert not hits, "Forbidden organization names found:\n" + "\n".join(hits)


def test_no_real_epic_schema_names(repo_root: Path, text_files) -> None:
    hits = []
    for path, text in text_files:
        for pat in EPIC_SCHEMA_NAMES:
            for m in pat.finditer(text):
                hits.append(f"{path.relative_to(repo_root)}: {m.group(0)!r}")
    assert not hits, "Real Epic-style schema names found:\n" + "\n".join(hits)


def test_no_phi_like_patterns(repo_root: Path, text_files) -> None:
    hits = []
    for path, text in text_files:
        rel = path.relative_to(repo_root)
        for m in SSN_RE.finditer(text):
            hits.append(f"{rel}: SSN-like {m.group(0)}")
        for m in PHONE_RE.finditer(text):
            hits.append(f"{rel}: phone-like {m.group(0)}")
        for m in EMAIL_RE.finditer(text):
            email = m.group(0)
            # Allow a reserved example.com address if a future day needs one.
            if email.lower().endswith("@example.com"):
                continue
            hits.append(f"{rel}: email {email}")
    assert not hits, "PHI-like content found:\n" + "\n".join(hits)


def test_disclaimer_present(repo_root: Path) -> None:
    text = (repo_root / "README.md").read_text(encoding="utf-8")
    assert "synthetic" in text.lower()
    assert "not affiliated" in text.lower()
    assert "not" in text.lower() and "epic" in text.lower()
