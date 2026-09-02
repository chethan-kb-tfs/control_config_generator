# Databricks SQL Insert Generator

A simple local Flask app that generates Databricks SQL `INSERT` statements for
`control_table_test` and `config_table_test` based on user input. It does
**not** connect to Databricks or execute any SQL — it only produces text you
can copy.

## Project structure

```
db_sql_generator/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

## Setup & run

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

## Using the app

### 1. Control Table Generator
- Fill in `src_sys_cd`, `target_bucket`, `primary_key`, `crt_by`, `upt_by`.
- Add one or more table names with **+ Add Table**.
- Clicking **Generate SQL** produces one `INSERT INTO control_table_test`
  statement with an `initial` (overwrite) row and a `delta` (append) row for
  every table name entered.

### 2. Config Table Generator
- Fill in `src_sys_cd`.
- Add one or more table configurations with **+ Add Table**, each with
  `table_name`, `src_table_path`, `spark_view_name`,
  `sql_filepaths_csv_str_full`, `sql_filepaths_csv_str_incr`, `uc`,
  `uc_schema`, `uc_table`.
- Clicking **Generate SQL** produces one `INSERT INTO config_table_test`
  statement with a `raw_table_config` row and a `sql_config` row for every
  table configuration entered.

### Notes
- Empty optional fields are generated as `NULL`.
- Single quotes in your input are automatically escaped for SQL safety.
- Use **Copy SQL** to copy each generated statement to your clipboard.
- Use **Clear Form** to reset everything back to a single empty row in each
  section.
