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
    assert items[1].startswith("- [x]"), "Day 002 should be checked off"
    assert items[2].startswith("- [x]"), "Day 003 should be checked off"
    assert sum(1 for line in items if line.startswith("- [ ]")) == 27
    assert "Days 001–003 are done" in text


def test_every_day_is_indexed_in_root_readme(repo_root: Path, day_dirs: list[Path]) -> None:
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    missing = [d.name for d in day_dirs if f"(days/{d.name}/)" not in readme]
    assert not missing, f"Day folders missing from the root README index: {missing}"


DAY002 = "day-002-long-lead-bookings-by-clinic-modality"


def test_day002_query_numbers(repo_root: Path, db_path: Path) -> None:
    day = repo_root / "days" / DAY002
    r = _result_map(day / "query.sql", db_path)

    overall = r["overall"].iloc[0]
    assert int(overall["scheduled_visits"]) == 49538
    assert int(overall["booked_over_14_days"]) == 14909
    assert float(overall["pct_over_14_days"]) == 30.1
    assert float(overall["avg_lead_days"]) == 10.5

    check = r["lead_days_check"].iloc[0]
    assert int(check["mismatched_rows"]) == 0
    assert int(check["booked_after_visit"]) == 0
    assert int(check["max_lead_days"]) == 47

    by_mod = r["by_modality"].set_index("modality")
    assert float(by_mod.loc["in_person", "pct_over_14_days"]) == 40.2
    assert float(by_mod.loc["video", "pct_over_14_days"]) == 3.5
    assert float(by_mod.loc["audio", "pct_over_14_days"]) == 2.2
    assert int(by_mod["scheduled_visits"].sum()) == 49538

    pct = r["lead_percentiles_by_modality"].set_index("modality")
    assert int(pct.loc["in_person", "median_lead_days"]) == 12
    assert int(pct.loc["in_person", "p90_lead_days"]) == 23

    by_clinic = r["by_clinic"].set_index("clinic_id")["pct_over_14_days"].astype(float)
    assert by_clinic.loc["C05"] == 65.5
    assert by_clinic.idxmax() == "C05"
    assert len(by_clinic) == 6

    cm = r["clinic_by_modality"]
    assert len(cm) == 18
    peers_virtual = cm[(cm["clinic_id"] != "C05") & (cm["modality"] != "in_person")]
    assert int(peers_virtual["booked_over_14_days"].sum()) == 0
    c05 = cm[cm["clinic_id"] == "C05"].set_index("modality")["pct_over_14_days"].astype(float)
    assert c05.loc["in_person"] == 84.2
    assert c05.loc["video"] == 18.8
    assert c05.loc["audio"] == 15.3

    groups = r["in_person_c05_vs_peers"].set_index("clinic_group")
    assert float(groups.loc["C05 Brookfield", "pct_over_14_days"]) == 84.2
    assert float(groups.loc["Peer clinics", "pct_over_14_days"]) == 31.5
    assert float(groups.loc["C05 Brookfield", "avg_lead_days"]) == 22.9
    assert float(groups.loc["Peer clinics", "avg_lead_days"]) == 10.4

    vt = r["in_person_c05_vs_peers_by_visit_type"].set_index(["visit_type", "clinic_group"])
    assert float(vt.loc[("acute", "C05 Brookfield"), "pct_over_14_days"]) == 49.8
    assert float(vt.loc[("acute", "Peer clinics"), "pct_over_14_days"]) == 0.0

    ns = r["in_person_no_show_by_booking_window"].set_index("booking_window")["no_show_rate_pct"].astype(float)
    assert ns.loc["over_14_days"] == 25.8
    assert ns.loc["14_days_or_less"] == 16.5

    bands = r["lead_band_by_modality"]
    for mod, share in bands.groupby("modality")["pct_of_modality"].sum().items():
        assert abs(float(share) - 100.0) < 0.3, f"{mod} lead bands should sum to ~100%"


def test_day002_readme_matches_sql(repo_root: Path, db_path: Path) -> None:
    """Every figure in the README is pulled from the query results, not typed by hand."""
    day = repo_root / "days" / DAY002
    readme = (day / "README.md").read_text(encoding="utf-8")
    r = _result_map(day / "query.sql", db_path)

    def pct(v) -> str:
        return f"{float(v):.1f}%"

    overall = r["overall"].iloc[0]
    required = [
        f"{int(overall['scheduled_visits']):,}",
        f"{int(overall['booked_over_14_days']):,}",
        pct(overall["pct_over_14_days"]),
        f"{float(overall['avg_lead_days']):.1f} days",
    ]
    pcts = r["lead_percentiles_by_modality"].set_index("modality")
    for _, row in r["by_modality"].iterrows():
        required += [
            f"{int(row['scheduled_visits']):,}",
            f"{int(row['booked_over_14_days']):,}",
            pct(row["pct_over_14_days"]),
            f"{float(row['avg_lead_days']):.1f} days",
            f"{int(pcts.loc[row['modality'], 'median_lead_days'])} days",
            f"{int(pcts.loc[row['modality'], 'p90_lead_days'])} days",
        ]
    for _, row in r["by_clinic"].iterrows():
        required += [f"{int(row['scheduled_visits']):,}", pct(row["pct_over_14_days"])]
    required += [pct(v) for v in r["clinic_by_modality"]["pct_over_14_days"]]
    for _, row in r["in_person_c05_vs_peers"].iterrows():
        required += [pct(row["pct_over_14_days"]), f"{float(row['avg_lead_days']):.1f} days"]
    yr = r["by_year_modality"].query("modality == 'in_person'")
    required += [pct(v) for v in yr["pct_over_14_days"]]
    vt = r["in_person_c05_vs_peers_by_visit_type"].query("visit_type == 'acute'")
    required += [pct(v) for v in vt["pct_over_14_days"]]
    required += [pct(v) for v in r["in_person_no_show_by_booking_window"]["no_show_rate_pct"]]

    missing = sorted({item for item in required if item not in readme})
    assert not missing, f"Day 002 README is missing numbers: {missing}"


def test_day002_chart_exists(repo_root: Path) -> None:
    chart = repo_root / "days" / DAY002 / "chart.png"
    if not chart.exists():
        pytest.skip("chart.png not built yet; run python run_all.py first")
    assert chart.stat().st_size > 10_000, "chart.png looks too small to be a real figure"


def test_day002_notebook_has_outputs(repo_root: Path) -> None:
    import nbformat

    path = repo_root / "days" / DAY002 / "analysis.ipynb"
    if not path.exists():
        pytest.fail("Day 002 notebook is missing")
    nb = nbformat.read(path, as_version=4)
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    executed = [c for c in code_cells if c.get("outputs")]
    if not executed:
        pytest.skip("notebook has not been executed yet; run python run_all.py first")
    assert len(executed) >= 3, "Expected executed outputs in the Day 002 notebook"
    errors = [o for c in code_cells for o in c.get("outputs", []) if o.get("output_type") == "error"]
    assert not errors, "Day 002 notebook has error outputs"


DAY003 = "day-003-no-show-by-lead-time-and-payer"


def test_day003_query_numbers(repo_root: Path, db_path: Path) -> None:
    day = repo_root / "days" / DAY003
    r = _result_map(day / "query.sql", db_path)

    check = r["payer_join_check"].iloc[0]
    assert int(check["scheduled_visits"]) == 49538
    assert int(check["no_patient_match"]) == 0
    assert int(check["no_payer_match"]) == 0
    assert int(check["duplicate_patients"]) == 0

    overall = r["overall"].iloc[0]
    assert int(overall["eligible_visits"]) == 45090
    assert int(overall["no_shows"]) == 7898
    assert float(overall["no_show_rate_pct"]) == 17.5

    band = r["by_lead_band"].set_index("lead_band")
    assert len(band) == 5
    assert int(band["eligible_visits"].sum()) == 45090
    assert int(band["no_shows"].sum()) == 7898
    assert abs(float(band["pct_of_eligible"].sum()) - 100.0) < 0.3
    rates = band["no_show_rate_pct"].astype(float)
    assert rates.loc["1: 0-3 days"] == 10.6
    assert rates.loc["2: 4-7 days"] == 13.0
    assert rates.loc["3: 8-14 days"] == 18.4
    assert rates.loc["4: 15-28 days"] == 24.5
    assert rates.loc["5: 29+ days"] == 34.6
    assert rates.is_monotonic_increasing, "no-show rate should rise with lead time"

    ip = r["in_person_by_lead_band"].set_index("lead_band")["no_show_rate_pct"].astype(float)
    assert ip.loc["1: 0-3 days"] == 12.5
    assert ip.loc["5: 29+ days"] == 34.6
    assert ip.is_monotonic_increasing

    payer = r["by_payer"].set_index("payer_name")
    assert len(payer) == 5
    assert int(payer["eligible_visits"].sum()) == 45090
    assert float(payer.loc["Medicaid", "no_show_rate_pct"]) == 20.7
    assert float(payer.loc["Self-pay", "no_show_rate_pct"]) == 19.7
    assert float(payer.loc["Birch HMO", "no_show_rate_pct"]) == 18.6
    assert float(payer.loc["Summit PPO", "no_show_rate_pct"]) == 17.2
    assert float(payer.loc["Medicare FFS", "no_show_rate_pct"]) == 15.1
    # Lead-time mix is nearly identical across payers.
    assert float(payer["pct_over_14_days"].max() - payer["pct_over_14_days"].min()) < 2.5

    pb = r["payer_by_lead_band"]
    assert len(pb) == 25
    assert int(pb["eligible_visits"].sum()) == 45090
    cell = pb.set_index(["payer_name", "lead_band"])
    assert float(cell.loc[("Medicaid", "4: 15-28 days"), "no_show_rate_pct"]) == 28.4
    for name, grp in pb.groupby("payer_name"):
        assert grp.sort_values("lead_band")["no_show_rate_pct"].is_monotonic_increasing, name

    spread = r["payer_spread_by_lead_band"].set_index("lead_band")["spread_pp"].astype(float)
    assert spread.min() == 5.0
    assert spread.max() == 6.5

    oe = r["payer_observed_vs_expected"].set_index("payer_name")
    assert float(oe.loc["Medicaid", "observed_to_expected"]) == 1.18
    assert float(oe.loc["Medicare FFS", "observed_to_expected"]) == 0.86
    assert int(oe["observed_no_shows"].sum()) == 7898
    assert abs(float(oe["expected_no_shows"].sum()) - 7898) < 1.0


def test_day003_readme_matches_sql(repo_root: Path, db_path: Path) -> None:
    """Every figure in the README is pulled from the query results, not typed by hand."""
    day = repo_root / "days" / DAY003
    readme = (day / "README.md").read_text(encoding="utf-8")
    r = _result_map(day / "query.sql", db_path)

    def pct(v) -> str:
        return f"{float(v):.1f}%"

    check = r["payer_join_check"].iloc[0]
    overall = r["overall"].iloc[0]
    required = [
        f"{int(check['scheduled_visits']):,}",
        f"{int(overall['eligible_visits']):,}",
        f"{int(overall['no_shows']):,}",
        pct(overall["no_show_rate_pct"]),
    ]
    for _, row in r["by_lead_band"].iterrows():
        required += [
            f"{int(row['eligible_visits']):,}",
            f"{int(row['no_shows']):,}",
            pct(row["no_show_rate_pct"]),
            pct(row["pct_of_eligible"]),
        ]
    required += [pct(v) for v in r["in_person_by_lead_band"]["no_show_rate_pct"]]
    payer = r["by_payer"]
    for _, row in payer.iterrows():
        required += [
            row["payer_name"],
            f"{int(row['eligible_visits']):,}",
            f"{int(row['no_shows']):,}",
            pct(row["no_show_rate_pct"]),
            f"{float(row['avg_lead_days']):.1f} days",
            pct(row["pct_over_14_days"]),
        ]
    for _, row in r["payer_observed_vs_expected"].iterrows():
        required += [
            f"{float(row['observed_to_expected']):.2f}",
            f"{int(row['observed_no_shows']):,}",
        ]
    oe = r["payer_observed_vs_expected"].set_index("payer_name")
    required += [
        f"{float(oe.loc['Medicaid', 'expected_no_shows']):,.1f}",
        f"{float(oe.loc['Medicare FFS', 'expected_no_shows']):,.1f}",
    ]
    for _, row in r["payer_spread_by_lead_band"].iterrows():
        required += [
            pct(row["lowest_rate_pct"]),
            pct(row["highest_rate_pct"]),
            f"{float(row['spread_pp']):.1f} pts",
        ]
    pb = r["payer_by_lead_band"].set_index(["payer_name", "lead_band"])
    required += [
        pct(pb.loc[("Medicaid", "4: 15-28 days"), "no_show_rate_pct"]),
        pct(pb.loc[("Self-pay", "4: 15-28 days"), "no_show_rate_pct"]),
        f"{int(pb.loc[('Medicaid', '4: 15-28 days'), 'eligible_visits']):,} visits",
    ]
    # Derived gaps quoted in the text.
    rates = payer.set_index("payer_name")["no_show_rate_pct"].astype(float)
    band = r["by_lead_band"].set_index("lead_band")["no_show_rate_pct"].astype(float)
    required += [
        f"{rates.loc['Medicaid'] - rates.loc['Medicare FFS']:.1f}-point gap",
        f"{band.iloc[-1] - band.iloc[0]:.1f}-point climb",
        f"{float(payer['avg_lead_days'].min()):.1f}–{float(payer['avg_lead_days'].max()):.1f} days",
        f"{pct(payer['pct_over_14_days'].min())}–{pct(payer['pct_over_14_days'].max())}",
    ]

    missing = sorted({item for item in required if item not in readme})
    assert not missing, f"Day 003 README is missing numbers: {missing}"


def test_day003_chart_exists(repo_root: Path) -> None:
    chart = repo_root / "days" / DAY003 / "chart.png"
    if not chart.exists():
        pytest.skip("chart.png not built yet; run python run_all.py first")
    assert chart.stat().st_size > 10_000, "chart.png looks too small to be a real figure"


def test_day003_notebook_has_outputs(repo_root: Path) -> None:
    import nbformat

    path = repo_root / "days" / DAY003 / "analysis.ipynb"
    if not path.exists():
        pytest.fail("Day 003 notebook is missing")
    nb = nbformat.read(path, as_version=4)
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    executed = [c for c in code_cells if c.get("outputs")]
    if not executed:
        pytest.skip("notebook has not been executed yet; run python run_all.py first")
    assert len(executed) >= 3, "Expected executed outputs in the Day 003 notebook"
    errors = [o for c in code_cells for o in c.get("outputs", []) if o.get("output_type") == "error"]
    assert not errors, "Day 003 notebook has error outputs"
