// ---------------------------------------------------------------------------
// Databricks SQL Insert Generator - Frontend Logic
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
    const controlList = document.getElementById("control-table-list");
    const configEntryList = document.getElementById("config-entry-list");
    const controlEntryTemplate = document.getElementById("control-entry-template");
    const configEntryTemplate = document.getElementById("config-entry-template");
    const configGroupTemplate = document.getElementById("config-table-row-template");
    const rawConfigRowTemplate = document.getElementById("raw-config-row-template");

    // -----------------------------------------------------------------
    // Row creation helpers
    // -----------------------------------------------------------------

    function addControlEntry() {
        const node = controlEntryTemplate.content.cloneNode(true);
        const entry = node.querySelector(".control-entry");

        entry.querySelector(".remove-control-entry").addEventListener("click", () => {
            entry.remove();
        });

        controlList.appendChild(entry);
    }

    function addRawConfigRow(group) {
        const node = rawConfigRowTemplate.content.cloneNode(true);
        const row = node.querySelector(".raw-config-row");

        row.querySelector(".remove-raw-config").addEventListener("click", () => {
            row.remove();
        });

        group.querySelector(".raw-config-list").appendChild(row);
    }

    function addConfigTableGroup(configTableListEl) {
        const node = configGroupTemplate.content.cloneNode(true);
        const group = node.querySelector(".config-table-group");

        group.querySelector(".remove-config-table").addEventListener("click", () => {
            group.remove();
        });

        group.querySelector(".add-raw-config").addEventListener("click", () => {
            addRawConfigRow(group);
        });

        configTableListEl.appendChild(group);

        // Every new table starts with one raw config row to fill in.
        addRawConfigRow(group);
    }

    function addConfigEntry() {
        const node = configEntryTemplate.content.cloneNode(true);
        const entry = node.querySelector(".config-entry");
        const tableListEl = entry.querySelector(".config-table-list");

        entry.querySelector(".remove-config-entry").addEventListener("click", () => {
            entry.remove();
        });

        entry.querySelector(".add-config-table").addEventListener("click", () => {
            addConfigTableGroup(tableListEl);
        });

        configEntryList.appendChild(entry);

        // Every new entry starts with one table to fill in.
        addConfigTableGroup(tableListEl);
    }

    // Start with one entry in each dynamic list
    addControlEntry();
    addConfigEntry();

    document.getElementById("add-control-entry").addEventListener("click", () => {
        addControlEntry();
    });

    document.getElementById("add-config-entry").addEventListener("click", () => {
        addConfigEntry();
    });

    // -----------------------------------------------------------------
    // Data collection
    // -----------------------------------------------------------------

    function collectControlData() {
        const entryEls = Array.from(document.querySelectorAll(".control-entry"));

        const entries = entryEls.map((entry) => ({
            src_sys_cd: entry.querySelector(".ctl-src-sys-cd").value,
            table_name: entry.querySelector(".ctl-table-name").value,
            target_bucket: entry.querySelector(".ctl-target-bucket").value,
            primary_key: entry.querySelector(".ctl-primary-key").value,
            crt_by: entry.querySelector(".ctl-crt-by").value,
            upt_by: entry.querySelector(".ctl-upt-by").value,
        }));

        return { entries: entries };
    }

    function collectConfigData() {
        const entryEls = Array.from(document.querySelectorAll(".config-entry"));

        const entries = entryEls.map((entryEl) => {
            const groupEls = Array.from(entryEl.querySelectorAll(".config-table-group"));

            const table_groups = groupEls.map((group) => {
                const rawRows = Array.from(group.querySelectorAll(".raw-config-row"));
                const raw_configs = rawRows.map((row) => ({
                    src_table_path: row.querySelector(".raw-src-table-path").value,
                    spark_view_name: row.querySelector(".raw-spark-view-name").value,
                    uc: row.querySelector(".raw-uc").value,
                    uc_schema: row.querySelector(".raw-uc-schema").value,
                    uc_table: row.querySelector(".raw-uc-table").value,
                }));

                return {
                    table_name: group.querySelector(".cfg-table-name").value,
                    raw_configs: raw_configs,
                    sql_config: {
                        sql_filepaths_csv_str_full: group.querySelector(".cfg-sql-full").value,
                        sql_filepaths_csv_str_incr: group.querySelector(".cfg-sql-incr").value,
                        uc: group.querySelector(".cfg-sqlcfg-uc").value,
                        uc_schema: group.querySelector(".cfg-sqlcfg-uc-schema").value,
                        uc_table: group.querySelector(".cfg-sqlcfg-uc-table").value,
                    },
                };
            });

            return {
                src_sys_cd: entryEl.querySelector(".cfg-src-sys-cd").value,
                table_groups: table_groups,
            };
        });

        return { entries: entries };
    }

    // -----------------------------------------------------------------
    // Validation display
    // -----------------------------------------------------------------

    function renderErrors(containerId, errors) {
        const container = document.getElementById(containerId);
        container.innerHTML = "";
        errors.forEach((msg) => {
            const div = document.createElement("div");
            div.className = "error-msg";
            div.textContent = msg;
            container.appendChild(div);
        });
    }

    // -----------------------------------------------------------------
    // Generate SQL
    // -----------------------------------------------------------------

    document.getElementById("generate-btn").addEventListener("click", async () => {
        const payload = {
            control: collectControlData(),
            config: collectConfigData(),
        };

        let data;
        try {
            const response = await fetch("/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            data = await response.json();
        } catch (err) {
            showToast("Error contacting server. Is the Flask app running?");
            console.error(err);
            return;
        }

        renderErrors("control-errors", data.control_errors || []);
        renderErrors("config-errors", data.config_errors || []);

        const outputSection = document.getElementById("output-section");
        const controlOutput = document.getElementById("control-output");
        const configOutput = document.getElementById("config-output");

        controlOutput.value = data.control_sql || "";
        configOutput.value = data.config_sql || "";

        const hasAnyOutput = data.control_sql || data.config_sql;
        outputSection.style.display = hasAnyOutput ? "flex" : "none";

        if (hasAnyOutput) {
            outputSection.scrollIntoView({ behavior: "smooth", block: "start" });
        }

        const totalErrors = (data.control_errors || []).length + (data.config_errors || []).length;
        if (totalErrors > 0) {
            showToast(`Fix ${totalErrors} validation issue(s) above.`);
        } else {
            showToast("SQL generated successfully.");
        }
    });

    // -----------------------------------------------------------------
    // Copy SQL buttons
    // -----------------------------------------------------------------

    document.querySelectorAll(".btn-copy").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const targetId = btn.getAttribute("data-target");
            const textarea = document.getElementById(targetId);
            if (!textarea.value) {
                showToast("Nothing to copy yet.");
                return;
            }
            try {
                await navigator.clipboard.writeText(textarea.value);
                showToast("Copied to clipboard.");
            } catch (err) {
                // Fallback for browsers without Clipboard API access
                textarea.select();
                document.execCommand("copy");
                showToast("Copied to clipboard.");
            }
        });
    });

    // -----------------------------------------------------------------
    // Clear form
    // -----------------------------------------------------------------

    document.getElementById("clear-btn").addEventListener("click", () => {
        document.querySelectorAll('.container input[type="text"]').forEach((el) => {
            el.value = "";
        });
        document.querySelectorAll(".container select").forEach((el) => {
            el.selectedIndex = 0;
        });

        controlList.innerHTML = "";
        configEntryList.innerHTML = "";
        addControlEntry();
        addConfigEntry();

        document.getElementById("control-errors").innerHTML = "";
        document.getElementById("config-errors").innerHTML = "";

        document.getElementById("output-section").style.display = "none";
        document.getElementById("control-output").value = "";
        document.getElementById("config-output").value = "";

        showToast("Form cleared.");
    });

    // -----------------------------------------------------------------
    // Toast helper
    // -----------------------------------------------------------------

    let toastTimeout;
    function showToast(message) {
        const toast = document.getElementById("toast");
        toast.textContent = message;
        toast.classList.add("show");
        clearTimeout(toastTimeout);
        toastTimeout = setTimeout(() => {
            toast.classList.remove("show");
        }, 2600);
    }
});
