# Alteryx: Rebuilding C1 and C2 and Reconciling with SQL

Two of the SQL controls (C1 and C2) were rebuilt in Alteryx Designer to check that a
second tool gives the same result as the SQL. Built on the 30-day Alteryx Designer trial
(Windows only).

## Input
`gold_transfer_cashout.csv`, exported from Databricks (see the end of
`sql/05_controls.sql`). The file is not committed because of its size. Place it in the
same folder as the workflow before opening it. The SQL side and the Alteryx side were run
on the same filtered population, so the two results are directly comparable.

## Workflow: `controls_C1_C2.yxmd`

| # | Tool | Configuration |
|---|---|---|
| 1 | **Input Data** | `gold_transfer_cashout.csv` (first row contains field names) |
| 2 | **Select** | Types set: `amount`, balances → Double. `step`, `is_fraud`, `txn_id` → Int64 |
| 3 | **Filter** (C1) | `[type] = "TRANSFER" AND [amount] >= 200000` |
| 4 | **Formula** (on C1 True output) | New field `control_name` = `"C1_high_value_transfer"` |
| 5 | **Filter** (C2), connected to Select | `[type] IN ("TRANSFER","CASH_OUT") AND [oldbalance_orig] > 0 AND [newbalance_orig] = 0 AND [amount] >= [oldbalance_orig]` |
| 6 | **Formula** (on C2 True output) | `control_name` = `"C2_account_drained"` |
| 7 | **Union** | Combines the C1 and C2 outputs |
| 8 | **Summarize** | Grouped by `control_name`. Count of `txn_id` → `flagged`, sum of `is_fraud` → `frauds_caught` |
| 9 | **Formula** | `precision_pct` = `100 * [frauds_caught] / [flagged]` |
| 10 | **Output Data** | `alteryx_control_results.csv` |
| 11 | **Browse** | Placed after steps 8 and 9 to capture intermediate results |

## Reconciliation

| Control | SQL flagged | Alteryx flagged | SQL frauds caught | Alteryx frauds caught | Match? |
|---|---|---|---|---|---|
| C1 | 409,110 | 409,110 | 2,740 | 2,740 | Exact |
| C2 | 1,188,074 | 1,188,074 | 8,012 | 8,012 | Exact |

Both controls reconciled exactly, with no discrepancy to investigate. If numbers differ
in a rebuild like this, the usual causes are data types (text vs number), decimal
rounding on `= 0`, or different row populations on the two sides.

## Files
- `controls_C1_C2.yxmd`: the workflow
- `docs/screenshots/alteryx_workflow.png`: the full canvas and Browse results
- The reconciliation table is repeated in the README