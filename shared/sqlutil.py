"""Helpers for named SQL query files used by each day's folder."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

NAME_RE = re.compile(r"/\*\s*name:\s*([a-zA-Z0-9_]+)\s*\*/")


def split_named_queries(sql_text: str) -> list[tuple[str, str]]:
    """Parse `/* name: foo */ ...;` blocks from a .sql file."""
    text = sql_text.strip()
    if not text:
        return []
    matches = list(NAME_RE.finditer(text))
    if not matches:
        # Fall back to a single unnamed statement (or several split by semicolon).
        parts = [s.strip() for s in text.split(";") if s.strip() and not set(s.strip()) <= set("-/* ")]
        return [(f"query_{i+1}", p) for i, p in enumerate(parts)]

    named: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip().rstrip(";").strip()
        if body:
            named.append((m.group(1), body))
    return named


def run_sql_file(sql_path: Path, db_path: Path) -> list[tuple[str, list[str], list[tuple]]]:
    """Run every named query in a file. Returns (name, columns, rows)."""
    queries = split_named_queries(sql_path.read_text(encoding="utf-8"))
    if not queries:
        raise ValueError(f"No SQL statements found in {sql_path}")
    results = []
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        for name, sql in queries:
            cur = conn.execute(sql)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = [tuple(r) for r in cur.fetchall()]
            results.append((name, cols, rows))
    return results
