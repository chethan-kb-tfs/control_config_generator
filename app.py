"""
Databricks SQL Insert Generator
--------------------------------
A simple local Flask app that generates Databricks SQL INSERT statements
for `control_table_test` and `config_table_test` based on user input.

This application does NOT connect to Databricks and does NOT execute any
SQL. It only builds INSERT statement text for the user to copy.
"""

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def esc(value):
    """Escape single quotes for safe SQL string literals."""
    if value is None:
        return ""
    return str(value).replace("'", "''")


def sql_str(value):
    """Return a quoted SQL string literal, or NULL if the value is empty."""
    if value is None:
        return "NULL"
    value = str(value).strip()
    if value == "":
        return "NULL"
    return f"'{esc(value)}'"


def sql_str_allow_empty(value):
    """Return a quoted SQL string literal even for empty strings (never NULL)."""
    if value is None:
        value = ""
    return f"'{esc(value)}'"


def sql_raw(value):
    """Return a raw (unquoted) SQL token, e.g. for numbers or literal NULL/TRUE."""
    return str(value)


# ---------------------------------------------------------------------------
# Control Table Generator
# ---------------------------------------------------------------------------

CONTROL_COLUMNS = [
    "project", "extract_type", "src_sys_cd", "table_name", "is_active",
    "load_type", "load_group", "target_bucket", "partition_cols", "primary_key",
    "athena_db_name", "status_flag", "timeout", "last_run_timestamp",
    "pre_proc_script_path", "pre_proc_args", "post_proc_script_path",
    "post_proc_args", "write_mode", "optimize", "vaccum", "crt_dt", "upt_dt",
    "crt_by", "upt_by", "row_md5", "registry_schema_name", "validate_schema",
    "gen_symlink", "parallel_read_config", "cdc_config", "write_format",
    "write_config", "filter_condn", "athena_partition_refresh", "vacuum_group",
    "optional_check", "repartition_val", "uc_flag", "uc", "uc_schema",
    "uc_table", "natural_key", "dw_src_key",
]


def build_control_row(src_sys_cd, table_name, target_bucket, primary_key,
                       crt_by, upt_by, load_type, write_mode):
    values = {
        "project": sql_str("cdw_to_edp"),
        "extract_type": sql_str("Dataframe"),
        "src_sys_cd": sql_str(src_sys_cd),
        "table_name": sql_str(table_name),
        "is_active": sql_str("Y"),
        "load_type": sql_str(load_type),
        "load_group": sql_raw(2),
        "target_bucket": sql_str(target_bucket),
        "partition_cols": sql_str("src_sys_cd"),
        "primary_key": sql_str(primary_key),
        "athena_db_name": sql_str("tfsdl_edp_sales"),
        "status_flag": sql_str("true"),
        "timeout": sql_raw(90),
        "last_run_timestamp": "NULL",
        "pre_proc_script_path": "NULL",
        "pre_proc_args": "NULL",
        "post_proc_script_path": "NULL",
        "post_proc_args": "NULL",
        "write_mode": sql_str(write_mode),
        "optimize": sql_str("true"),
        "vaccum": sql_str("false"),
        "crt_dt": "NULL",
        "upt_dt": "NULL",
        "crt_by": sql_str(crt_by),
        "upt_by": sql_str(upt_by),
        "row_md5": "NULL",
        "registry_schema_name": sql_str("tfsdl_edp_common_dims"),
        "validate_schema": sql_str("Y"),
        "gen_symlink": sql_str("TRUE"),
        "parallel_read_config": "NULL",
        "cdc_config": "NULL",
        "write_format": sql_str("delta"),
        "write_config": "NULL",
        "filter_condn": sql_str_allow_empty(""),
        "athena_partition_refresh": sql_str("add_partition"),
        "vacuum_group": sql_raw(7),
        "optional_check": sql_str('{"hive_default":{"enable_check":"Y"}}'),
        "repartition_val": "NULL",
        "uc_flag": sql_str("N"),
        "uc": "NULL",
        "uc_schema": "NULL",
        "uc_table": "NULL",
        "natural_key": "NULL",
        "dw_src_key": "NULL",
    }
    ordered = [values[col] for col in CONTROL_COLUMNS]
    return "(\n    " + ",\n    ".join(ordered) + "\n)"


TARGET_BUCKET_OPTIONS = [
    "s3://tfsdl-edp-sales-test/",
    "s3://tfsdl-edp-common-dims-test/",
]

SRC_SYS_CD_OPTIONS = [
    "aa_e1_cn", "aa_e1_kr", "aa_jde_de", "aa_jde_uk", "aa_oms_us", "ampk",
    "ddw", "e1latam", "edw_abi", "edw_e1", "edw_gl", "euasw", "euibs",
    "gbl", "iscala_fin", "iscala_rus", "lcd_infor_newport",
    "lcd_infor_roskilde", "lcd_macola", "lcd_syspro_auburn",
    "lcd_syspro_miami", "lcd_syspro_rockwood", "led_baan",
    "led_syspro_singapore", "lpd_adj", "lsb", "oxaion", "roc",
]


def generate_control_sql(data):
    """
    Control Table Generator rules:
    - `data` contains multiple "entries". Each entry represents exactly one
      (src_sys_cd, table_name) combination, plus its own target_bucket /
      primary_key / crt_by / upt_by.
    - To add another table for the same src_sys_cd, or the same table_name
      under a different src_sys_cd, the caller just adds another entry.
    - Every entry produces exactly 2 rows: initial (overwrite) and delta
      (append).
    - All rows across all entries are combined into a single
      INSERT INTO control_table_test statement.
    """
    entries = data.get("entries", [])

    errors = []
    cleaned_entries = []

    for e_idx, entry in enumerate(entries, start=1):
        src_sys_cd = (entry.get("src_sys_cd") or "").strip()
        target_bucket = (entry.get("target_bucket") or "").strip()
        primary_key = (entry.get("primary_key") or "").strip()
        crt_by = (entry.get("crt_by") or "").strip()
        upt_by = (entry.get("upt_by") or "").strip()
        table_name = (entry.get("table_name") or "").strip()

        has_any_data = bool(
            src_sys_cd or target_bucket or primary_key or crt_by or upt_by or table_name
        )
        if not has_any_data:
            continue  # fully empty entry, skip silently

        prefix = f"Control Table entry {e_idx}"
        if not src_sys_cd:
            errors.append(f"{prefix}: src_sys_cd is required.")
        elif src_sys_cd not in SRC_SYS_CD_OPTIONS:
            errors.append(f"{prefix}: src_sys_cd must be selected from the dropdown list.")
        if not target_bucket:
            errors.append(f"{prefix}: target_bucket is required.")
        elif target_bucket not in TARGET_BUCKET_OPTIONS:
            errors.append(
                f"{prefix}: target_bucket must be one of: "
                + ", ".join(TARGET_BUCKET_OPTIONS)
            )
        if not primary_key:
            errors.append(f"{prefix}: primary_key is required.")
        if not crt_by:
            errors.append(f"{prefix}: crt_by is required.")
        if not upt_by:
            errors.append(f"{prefix}: upt_by is required.")
        if not table_name:
            errors.append(f"{prefix}: table_name is required.")

        cleaned_entries.append({
            "src_sys_cd": src_sys_cd,
            "target_bucket": target_bucket,
            "primary_key": primary_key,
            "crt_by": crt_by,
            "upt_by": upt_by,
            "table_name": table_name,
        })

    if not cleaned_entries:
        errors.append("Control Table: at least one entry is required.")

    if errors:
        return None, errors

    rows = []
    for entry in cleaned_entries:
        rows.append(build_control_row(
            entry["src_sys_cd"], entry["table_name"], entry["target_bucket"],
            entry["primary_key"], entry["crt_by"], entry["upt_by"],
            "initial", "overwrite"
        ))
        rows.append(build_control_row(
            entry["src_sys_cd"], entry["table_name"], entry["target_bucket"],
            entry["primary_key"], entry["crt_by"], entry["upt_by"],
            "delta", "append"
        ))

    columns_sql = ",\n    ".join(CONTROL_COLUMNS)
    sql = (
        "INSERT INTO control_table_test (\n    "
        + columns_sql
        + "\n)\nVALUES\n"
        + ",\n".join(rows)
        + ";"
    )
    return sql, []



# ---------------------------------------------------------------------------
# Config Table Generator
# ---------------------------------------------------------------------------

CONFIG_COLUMNS = [
    "project", "config_type", "src_sys_cd", "table_name", "data_table_format",
    "src_table_path", "spark_view_name", "sql_filepaths_csv_str_full",
    "sql_filepaths_csv_str_incr", "row_md5", "uc", "uc_schema", "uc_table",
]


def build_raw_table_config_row(src_sys_cd, table_name, src_table_path,
                                spark_view_name, uc, uc_schema, uc_table):
    values = {
        "project": sql_str("cdw_to_edp"),
        "config_type": sql_str("raw_table_config"),
        "src_sys_cd": sql_str(src_sys_cd),
        "table_name": sql_str(table_name),
        "data_table_format": sql_str("delta"),
        "src_table_path": sql_str(src_table_path),
        "spark_view_name": sql_str(spark_view_name),
        "sql_filepaths_csv_str_full": "NULL",
        "sql_filepaths_csv_str_incr": "NULL",
        "row_md5": "NULL",
        "uc": sql_str(uc),
        "uc_schema": sql_str(uc_schema),
        "uc_table": sql_str(uc_table),
    }
    ordered = [values[col] for col in CONFIG_COLUMNS]
    return "(\n    " + ",\n    ".join(ordered) + "\n)"


def build_sql_config_row(src_sys_cd, table_name, sql_filepaths_csv_str_full,
                          sql_filepaths_csv_str_incr, uc, uc_schema, uc_table):
    values = {
        "project": sql_str("cdw_to_edp"),
        "config_type": sql_str("sql_config"),
        "src_sys_cd": sql_str(src_sys_cd),
        "table_name": sql_str(table_name),
        "data_table_format": "NULL",
        "src_table_path": "NULL",
        "spark_view_name": "NULL",
        "sql_filepaths_csv_str_full": sql_str(sql_filepaths_csv_str_full),
        "sql_filepaths_csv_str_incr": sql_str(sql_filepaths_csv_str_incr),
        "row_md5": "NULL",
        "uc": sql_str(uc),
        "uc_schema": sql_str(uc_schema),
        "uc_table": sql_str(uc_table),
    }
    ordered = [values[col] for col in CONFIG_COLUMNS]
    return "(\n    " + ",\n    ".join(ordered) + "\n)"


def _process_table_groups(src_sys_cd, table_groups, entry_label, errors):
    """
    Validate and clean the table groups for one src_sys_cd entry.
    Returns a list of cleaned group dicts (mutates `errors` in place).
    """
    cleaned_groups = []
    for g_idx, group in enumerate(table_groups, start=1):
        table_name = (group.get("table_name") or "").strip()
        raw_configs_in = group.get("raw_configs", []) or []
        sql_config_in = group.get("sql_config", {}) or {}

        cleaned_raw_configs = []
        for r_idx, rc in enumerate(raw_configs_in, start=1):
            src_table_path = (rc.get("src_table_path") or "").strip()
            spark_view_name = (rc.get("spark_view_name") or "").strip()
            uc = (rc.get("uc") or "").strip()
            uc_schema = (rc.get("uc_schema") or "").strip()
            uc_table = (rc.get("uc_table") or "").strip()

            has_data = any([src_table_path, spark_view_name, uc, uc_schema, uc_table])
            if not has_data:
                continue

            if not table_name:
                errors.append(
                    f"{entry_label}, table {g_idx}, raw config {r_idx} "
                    f"has data but the table is missing table_name."
                )
                continue

            cleaned_raw_configs.append({
                "src_table_path": src_table_path,
                "spark_view_name": spark_view_name,
                "uc": uc,
                "uc_schema": uc_schema,
                "uc_table": uc_table,
            })

        sql_full = (sql_config_in.get("sql_filepaths_csv_str_full") or "").strip()
        sql_incr = (sql_config_in.get("sql_filepaths_csv_str_incr") or "").strip()
        sql_uc = (sql_config_in.get("uc") or "").strip()
        sql_uc_schema = (sql_config_in.get("uc_schema") or "").strip()
        sql_uc_table = (sql_config_in.get("uc_table") or "").strip()

        has_group_data = bool(table_name) or cleaned_raw_configs or any(
            [sql_full, sql_incr, sql_uc, sql_uc_schema, sql_uc_table]
        )
        if not has_group_data:
            continue  # fully empty table, skip silently

        if not table_name:
            errors.append(f"{entry_label}, table {g_idx}: table_name is required.")
            continue

        cleaned_groups.append({
            "table_name": table_name,
            "raw_configs": cleaned_raw_configs,
            "sql_config": {
                "sql_filepaths_csv_str_full": sql_full,
                "sql_filepaths_csv_str_incr": sql_incr,
                "uc": sql_uc,
                "uc_schema": sql_uc_schema,
                "uc_table": sql_uc_table,
            },
        })

    return cleaned_groups


def generate_config_sql(data):
    """
    Config Table Generator rules:
    - `data` contains multiple "entries", each with its own src_sys_cd
      (mirrors the Control Table Generator entry model). To add another
      table under the same src_sys_cd, or the same table under a different
      src_sys_cd, the caller just adds another table / another entry.
    - Each entry has multiple "tables", each keyed by a single table_name.
    - A table can have MULTIPLE raw_table_config rows (each with its own
      src_table_path / spark_view_name / uc / uc_schema / uc_table).
    - A table has EXACTLY ONE sql_config row (src_table_path and
      spark_view_name are NULL for that row), using the table's table_name.
    """
    entries = data.get("entries", [])

    errors = []
    cleaned_entries = []

    for e_idx, entry in enumerate(entries, start=1):
        src_sys_cd = (entry.get("src_sys_cd") or "").strip()
        table_groups = entry.get("table_groups", [])

        entry_label = f"Config Table entry {e_idx}"
        cleaned_groups = _process_table_groups(src_sys_cd, table_groups, entry_label, errors)

        has_any_data = bool(src_sys_cd) or bool(cleaned_groups)
        if not has_any_data:
            continue  # fully empty entry, skip silently

        if not src_sys_cd:
            errors.append(f"{entry_label}: src_sys_cd is required.")
        elif src_sys_cd not in SRC_SYS_CD_OPTIONS:
            errors.append(f"{entry_label}: src_sys_cd must be selected from the dropdown list.")

        if not cleaned_groups:
            errors.append(f"{entry_label}: at least one table with a table_name is required.")

        cleaned_entries.append({
            "src_sys_cd": src_sys_cd,
            "table_groups": cleaned_groups,
        })

    if not cleaned_entries:
        errors.append("Config Table: at least one entry is required.")

    if errors:
        return None, errors

    rows = []
    for entry in cleaned_entries:
        src_sys_cd = entry["src_sys_cd"]
        for group in entry["table_groups"]:
            table_name = group["table_name"]

            # Multiple raw_table_config rows per table.
            for rc in group["raw_configs"]:
                rows.append(build_raw_table_config_row(
                    src_sys_cd, table_name, rc["src_table_path"],
                    rc["spark_view_name"], rc["uc"], rc["uc_schema"], rc["uc_table"]
                ))

            # Exactly one sql_config row per table.
            sc = group["sql_config"]
            rows.append(build_sql_config_row(
                src_sys_cd, table_name, sc["sql_filepaths_csv_str_full"],
                sc["sql_filepaths_csv_str_incr"], sc["uc"], sc["uc_schema"], sc["uc_table"]
            ))

    columns_sql = ",\n    ".join(CONFIG_COLUMNS)
    sql = (
        "INSERT INTO config_table_test (\n    "
        + columns_sql
        + "\n)\nVALUES\n"
        + ",\n".join(rows)
        + ";"
    )
    return sql, []



# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        src_sys_cd_options=SRC_SYS_CD_OPTIONS,
        target_bucket_options=TARGET_BUCKET_OPTIONS,
    )


@app.route("/generate", methods=["POST"])
def generate():
    payload = request.get_json(silent=True) or {}

    result = {
        "control_sql": None,
        "config_sql": None,
        "control_errors": [],
        "config_errors": [],
    }

    control_data = payload.get("control")
    if control_data is not None:
        control_sql, control_errors = generate_control_sql(control_data)
        result["control_sql"] = control_sql
        result["control_errors"] = control_errors

    config_data = payload.get("config")
    if config_data is not None:
        config_sql, config_errors = generate_config_sql(config_data)
        result["config_sql"] = config_sql
        result["config_errors"] = config_errors

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
