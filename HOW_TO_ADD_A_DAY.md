# How to add a new day

Each day should be a small, genuine analysis: one business question, runnable SQL, an executed notebook, one chart, and a README whose numbers match the query output. Do not add a day that only tweaks wording.

## 1. Pick a topic

Use the next unchecked item in [BACKLOG.md](BACKLOG.md), or write a new one in the same style if a better question comes up. Stay inside this series' rules:

- synthetic data from `shared/clinic.db`, or a cited public CMS file
- no real patient data, no employer data
- no real Epic table or column names
- tools already in this repo: SQL, Python, Jupyter, Matplotlib (Tableau may be mentioned as a skill, but the day has to render on GitHub without Tableau)

## 2. Create the folder from the template

From the repo root:

```bash
python scripts/new_day.py short-kebab-slug --title "Human title"
```

This copies [`days/_template/`](days/_template/) to `days/day-00N-short-kebab-slug/` and fills in the day number on the README.

## 3. Write the analysis

- Put named queries in `query.sql` using blocks like `/* name: overall */`. `run_all.py` will save each result to `results/<name>.csv`.
- Use the notebook to run those questions (or the same SQL), explain the finding, and save a single clean chart as `chart.png` in the day folder.
- Keep the chart titled, labeled, and sourced. Note that the data are synthetic.

Relative path to the database from a day folder or from the notebook (when the working directory is the day folder):

```text
../../shared/clinic.db
```

## 4. Run and fill in the README

```bash
python run_all.py
```

Then edit the day's `README.md`:

- business question
- approach
- results, with the actual numbers from `results/` (counts, rates to one decimal)
- a short takeaway for a clinic manager, quality analyst, or revenue-cycle lead

If you change the generator, pass `--refresh-db` and update any day whose numbers moved.

## 5. Index, backlog, and tests

- Add a row to the days table in the root [README.md](README.md).
- Check the item off in [BACKLOG.md](BACKLOG.md).
- Run `pytest` from the repo root. Tests execute every day's SQL, check that README figures match the queries for day 001, and scan the repo for disallowed content.

## 6. Commit

Commit locally with a message that names the day and the finding, for example `Add day 002: 34% of in-person visits book more than 14 days out`. Publish to GitHub only when you are ready to share that day.
