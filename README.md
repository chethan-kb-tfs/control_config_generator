# Databricks SQL Insert Generator

A simple local Flask app that generates Databricks SQL `INSERT` statements for
`control_table_test` and `config_table_test` based on user input. It does
**not** connect to Databricks or execute any SQL — it only produces text you
can copy.

## Project structure

```
control_config_generator/
├── app.py
├── version.json
├── requirements.txt
├── install.bat
├── run.bat
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

## Windows quick start (recommended)

Two scripts are included so you don't have to remember any commands. They
both target one fixed, predictable location regardless of where you run them
from:

```
%USERPROFILE%\control_config_generator   (i.e. C:\Users\<you>\control_config_generator)
```

| Script | When to use it | What it does |
|---|---|---|
| `install.bat` | First time only | Clones this repo (branch `dev`) into `%USERPROFILE%\control_config_generator` if it isn't already there, then creates the virtual environment (if missing) and installs dependencies. |
| `run.bat` | Every time | Goes to the fixed install location, checks the `dev` branch on GitHub for a newer version and pulls it if found (reinstalling dependencies only if `requirements.txt` changed), reuses the existing virtual environment (creates it only if it's missing), starts the app, and opens it in Chrome. If GitHub can't be reached, it just starts the app with whatever is already on disk. |

You only need to download `install.bat` itself to get started — it clones
everything else for you. After that, double-click `run.bat` every time you
want to use the app — it always checks for and applies updates automatically
before starting, so there's no separate "update" step. You can run it from
`%USERPROFILE%\control_config_generator` directly, or from a shortcut to it
placed anywhere (e.g. your Desktop) — it always resolves to the same fixed
folder no matter where the shortcut lives.

`run.bat`:
- Checks whether the `venv` folder already exists — it only creates a new
  virtual environment if one isn't there yet, it never recreates it.
- Starts `app.py` in its own window.
- Opens `http://127.0.0.1:5000` in Chrome (falling back to your default
  browser if Chrome isn't found).

To stop the app, close the window that `run.bat` opened for it.

## Manual setup & run (macOS/Linux, or if you prefer not to use the .bat files)

1. Create and activate a virtual environment:

   ```
   python -m venv venv
   ```

   Windows:
   ```
   venv\Scripts\activate
   ```

   macOS/Linux:
   ```
   source venv/bin/activate
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Run the app:

   ```
   python app.py
   ```

4. Open your browser at:

   ```
   http://127.0.0.1:5000
   ```

## Versioning

`version.json` at the project root tracks the app's version, who last updated
it, and when:

```json
{
    "version": "1.0.0",
    "developed_by": "Chethan KB",
    "last_updated": "2026-09-02"
}
```

The running app reads this file and shows it in the footer of the page (and
at the `/version` endpoint as JSON). When you make changes, bump the
`version` and `last_updated` fields before committing — `run.bat` reports
the old and new version numbers when it pulls an update, and the footer will
reflect the new version the next time the app starts.

## Using the app

### 1. Control Table Generator
Each **entry** is exactly one `src_sys_cd` + `table_name` combination, along
with its own `target_bucket`, `primary_key`, `crt_by`, and `upt_by`.
- Click **+ Add Control Table Entry** to add another `src_sys_cd`/`table_name`
  combination — whether that's another table under the same `src_sys_cd`, the
  same table under a different `src_sys_cd`, or a totally new combination.
- Every entry generates exactly 2 rows: one `initial` (overwrite) row and one
  `delta` (append) row.
- All rows from all entries are combined into a single
  `INSERT INTO control_table_test` statement.

### 2. Config Table Generator
Each **entry** is its own `src_sys_cd`, containing one or more **tables**.
- Click **+ Add Config Entry** to add another `src_sys_cd`.
- Inside an entry, click **+ Add Table** to add a table
  (`table_name` + its raw configs + one shared SQL config).
- Inside a table, click **+ Add Raw Config** to add another
  `raw_table_config` row (`src_table_path`, `spark_view_name`, `uc`,
  `uc_schema`, `uc_table`) for that same table.
- Each table produces exactly **one** `sql_config` row (with
  `sql_filepaths_csv_str_full`, `sql_filepaths_csv_str_incr`, `uc`,
  `uc_schema`, `uc_table`; `src_table_path` and `spark_view_name` are `NULL`
  for that row) — regardless of how many raw configs it has.
- All rows from all entries/tables are combined into a single
  `INSERT INTO config_table_test` statement.

### Notes
- `src_sys_cd` and `target_bucket` are chosen from fixed dropdown lists.
- Empty optional fields are generated as `NULL`.
- Single quotes in your input are automatically escaped for SQL safety.
- Use **Copy SQL** to copy each generated statement to your clipboard.
- Use **Clear Form** to reset everything back to one empty entry in each
  section.
