# Healthcare Analytics Daily

A series of small, complete healthcare analytics exercises — one per day — written so they render on GitHub with nothing to install. Each day answers a realistic operations or quality question with SQL and Python, using the same synthetic clinic database.

Chensheng Wen is an Epic-certified (Cogito, Clarity, Caboodle) BI Specialist targeting healthcare data analyst, BI analyst, and Epic analyst roles, working in SQL, Python, Jupyter, and Tableau.

The latest entry is **[Day 003: No-show rate by lead-time band and payer](days/day-003-no-show-by-lead-time-and-payer/)**.

## Days

| Day | Date added | Title | Skills | Link |
|---:|---|---|---|---|
| 001 | 2026-11-25 | Monthly clinic no-show rate by visit type | SQL window functions, Python, Matplotlib | [day-001-monthly-no-show-by-visit-type](days/day-001-monthly-no-show-by-visit-type/) |
| 002 | 2026-11-26 | Share of visits booked more than 14 days out, by clinic and modality | SQL CASE and joins, ROW_NUMBER percentiles, Python, Matplotlib | [day-002-long-lead-bookings-by-clinic-modality](days/day-002-long-lead-bookings-by-clinic-modality/) |
| 003 | 2026-11-27 | No-show rate by lead-time band and payer | SQL CASE bands and joins, ROW_NUMBER, indirect standardization, Python, Matplotlib | [day-003-no-show-by-lead-time-and-payer](days/day-003-no-show-by-lead-time-and-payer/) |

Planned topics for later days are in [BACKLOG.md](BACKLOG.md). How to add the next day is in [HOW_TO_ADD_A_DAY.md](HOW_TO_ADD_A_DAY.md).

## Data and privacy

- **All clinic data in this repo is synthetic.** It is built by a seeded generator ([`shared/generate_synthetic.py`](shared/generate_synthetic.py), `SEED=42`) and describes no real patient, provider, clinic, or health system. Identifiers are zero-padded codes such as `P000001`. There are no names, dates of birth, addresses, phone numbers, medical record numbers, or other direct identifiers.
- A compact SQLite database lives at [`shared/clinic.db`](shared/clinic.db). The [data dictionary](shared/data_dictionary.md) lists every table, its grain, and row counts. A 500-row appointment preview is in [`shared/samples/appointments_sample.csv`](shared/samples/appointments_sample.csv).
- Some later days will add a small **public** CMS file (for example Medicare Telehealth Trends or Hospital Compare). Those files will be cited and stored under `shared/public/`. They are not patient-level data.
- Table and column names (`fact_appointment`, `dim_patient`, `fact_medication_order`, and so on) are generic inventions. They are **not** Epic's Clarity, Caboodle, or Willow schema, and this project is not affiliated with or endorsed by Epic Systems Corporation. When a day uses a "Willow-style" pharmacy question, that phrase refers to the business problem only.

## What's in a day

Each folder under [`days/`](days/) is meant to stand on its own:

- a short README with the business question, the approach, results that match the query output, and a takeaway for a clinic or hospital leader
- `query.sql` with named, runnable SQLite queries
- an executed Jupyter notebook (`analysis.ipynb`) whose outputs display on GitHub
- one clean chart as `chart.png`

## How to run

Requires Python 3.10+.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_all.py            # uses shared/clinic.db; add --refresh-db to regenerate it
pytest
```

To start the next day:

```bash
python scripts/new_day.py short-slug --title "Human title"
```

## Project structure

```
healthcare-analytics-daily/
├── README.md
├── BACKLOG.md                      # 30 planned day topics
├── HOW_TO_ADD_A_DAY.md
├── run_all.py                      # generate db, run SQL, execute notebooks
├── requirements.txt
├── shared/
│   ├── generate_synthetic.py       # seeded generator
│   ├── clinic.db                   # reusable SQLite database
│   ├── data_dictionary.md
│   └── samples/appointments_sample.csv
├── days/
│   ├── _template/                  # copied by scripts/new_day.py
│   ├── day-001-monthly-no-show-by-visit-type/
│   ├── day-002-long-lead-bookings-by-clinic-modality/
│   └── day-003-no-show-by-lead-time-and-payer/
├── scripts/new_day.py
└── tests/
```

## Related work

Larger, self-contained projects in the same portfolio:

- [Hybrid Clinic KPI Dashboard](https://github.com/wenchensheng/hybrid-clinic-kpi-dashboard) — virtual vs in-person primary care KPIs
- [Clinic Pocket Huddle](https://github.com/wenchensheng/clinic-pocket-huddle) — mobile no-show risk huddle
- [Telehealth Access Explorer](https://github.com/wenchensheng/telehealth-access-explorer) — CMS telehealth trends
- [Healthcare Reporting Warehouse](https://github.com/wenchensheng/healthcare-reporting-warehouse) — star schema, ETL, and monthly reports
