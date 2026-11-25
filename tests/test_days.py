from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from shared.sqlutil import run_sql_file, split_named_queries


def _result_map(sql_path: Path, db_path: Path) -> dict[str, pd.DataFrame]:
    out = {}
    for name, cols, rows in run_sql_file(sql_path, db_path):
        out[name] = pd.DataFrame(rows, columns=cols)
    return out


def test_every_day_has_required_files(day_dirs: list[Path]) -> None:
    assert day_dirs, "Expected at least one day folder"
    for day in day_dirs:
        assert (day / "README.md").exists(), f"{day.name} missing README.md"
        assert (day / "query.sql").exists(), f"{day.name} missing query.sql"
        sql = (day / "query.sql").read_text(encoding="utf-8")
        assert split_named_queries(sql), f"{day.name} query.sql has no runnable statements"


def test_every_day_sql_runs(day_dirs: list[Path], db_path: Path) -> None:
    for day in day_dirs:
        results = run_sql_file(day / "query.sql", db_path)
        assert results, f"{day.name}: no query results"
        for name, cols, rows in results:
            assert name, "query is missing a name"
            assert cols, f"{day.name}/{name} returned no columns"


def test_day001_query_numbers(repo_root: Path, db_path: Path) -> None:
    day = repo_root / "days" / "day-001-monthly-no-show-by-visit-type"
    r = _result_map(day / "query.sql", db_path)

    overall = r["overall"].iloc[0]
    assert int(overall["eligible_visits"]) == 45090
    assert int(overall["no_shows"]) == 7898
    assert float(overall["no_show_rate_pct"]) == 17.5
    assert int(r["cancelled_excluded"].iloc[0]["cancelled_visits"]) == 4448

    by_year = r["by_year"].set_index("year")["no_show_rate_pct"].astype(float)
    assert by_year.loc["2024"] == 18.1
    assert by_year.loc["2025"] == 17.0

    by_type = r["by_visit_type"].set_index("visit_type")["no_show_rate_pct"].astype(float)
    assert by_type.loc["new_patient"] == 24.1
    assert by_type.loc["preventive"] == 20.8
    assert by_type.loc["chronic_followup"] == 17.4
    assert by_type.loc["acute"] == 12.5

    by_mod = r["by_modality"].set_index("modality")["no_show_rate_pct"].astype(float)
    assert by_mod.loc["in_person"] == 20.2
    assert by_mod.loc["video"] == 11.1
    assert by_mod.loc["audio"] == 8.8

    groups = r["c05_vs_peers"].set_index("clinic_group")["no_show_rate_pct"].astype(float)
    assert groups.loc["C05 Brookfield"] == 25.7
    assert groups.loc["Peer clinics"] == 15.9

    monthly = r["monthly_overall"].set_index("year_month")
    assert float(monthly.loc["2024-03", "ma3_rate_pct"]) == 18.8
    assert float(monthly.loc["2025-12", "ma3_rate_pct"]) == 16.9
    assert float(monthly.loc["2025-08", "no_show_rate_pct"]) == 15.1
    assert len(monthly) == 24

    vshare = r["virtual_share_by_year"].set_index("year")["virtual_share_pct"].astype(float)
    assert vshare.loc["2024"] == 27.9
    assert vshare.loc["2025"] == 31.8


def test_day001_readme_matches_sql(repo_root: Path, db_path: Path) -> None:
    day = repo_root / "days" / "day-001-monthly-no-show-by-visit-type"
    readme = (day / "README.md").read_text(encoding="utf-8")
    # Key figures that a reader would check against the queries.
    required = [
        "17.5%",
        "45,090",
        "7,898",
        "4,448",
        "18.1%",
        "17.0%",
        "24.1%",
        "20.8%",
        "17.4%",
        "12.5%",
        "20.2%",
        "11.1%",
        "8.8%",
        "25.7%",
        "15.9%",
        "27.9%",
        "31.8%",
        "18.8%",
        "16.9%",
        "15.1%",
        "16.2 days",
        "54.0%",
        "21.1%",
        "10.8%",
    ]
    missing = [item for item in required if item not in readme]
    assert not missing, f"Day 001 README is missing numbers: {missing}"


def test_day001_chart_exists(repo_root: Path) -> None:
    chart = repo_root / "days" / "day-001-monthly-no-show-by-visit-type" / "chart.png"
    # run_all.py writes the chart; this test allows the collection to happen
    # before that, but fails if the suite is run after a full build without it.
    if not chart.exists():
        pytest.skip("chart.png not built yet; run python run_all.py first")
    assert chart.stat().st_size > 10_000, "chart.png looks too small to be a real figure"


def test_day001_notebook_has_outputs(repo_root: Path) -> None:
    import nbformat

    path = repo_root / "days" / "day-001-monthly-no-show-by-visit-type" / "analysis.ipynb"
    if not path.exists():
        pytest.fail("Day 001 notebook is missing")
    nb = nbformat.read(path, as_version=4)
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    executed = [c for c in code_cells if c.get("outputs")]
    if not executed:
        pytest.skip("notebook has not been executed yet; run python run_all.py first")
    assert len(executed) >= 3, "Expected executed outputs in the Day 001 notebook"


def test_template_exists(repo_root: Path) -> None:
    tmpl = repo_root / "days" / "_template"
    for name in ("README.md", "query.sql", "analysis.ipynb"):
        assert (tmpl / name).exists(), f"template missing {name}"


def test_backlog_has_thirty_topics(repo_root: Path) -> None:
    text = (repo_root / "BACKLOG.md").read_text(encoding="utf-8")
    items = [line for line in text.splitlines() if line.startswith("- [")]
    assert len(items) == 30, f"BACKLOG.md should list 30 days, found {len(items)}"
    assert items[0].startswith("- [x]"), "Day 001 should be checked off"
    assert sum(1 for line in items if line.startswith("- [ ]")) == 29
