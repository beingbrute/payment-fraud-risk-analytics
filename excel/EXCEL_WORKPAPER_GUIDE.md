# Excel Control-Testing Workpaper Guide

`control_testing_workpaper.xlsx` documents the testing of the five SQL controls (C1 to C5): PivotTable, XLOOKUP, conditional formatting and a chart. Built in Excel for the web.

## Sheet 1: `Summary` (one row per control)
| Column | Content |
|---|---|
| Control ID | C1 … C5 |
| Control objective | e.g. "Detect unusually large transfers for review" |
| Population | Transactions tested (e.g. all TRANSFER rows) |
| Test logic | Plain-English rule |
| Flagged | **XLOOKUP** from sheet `Results` |
| Frauds caught | **XLOOKUP** from `Results` |
| Precision % / Recall % | Formulas (precision = frauds caught / flagged; recall = frauds caught / 8,213 total frauds) |
| Conclusion | Effective / Partially effective / Ineffective, with reasoning |

Conditional formatting on Recall %: green at 40% or above, red below 20%, unformatted between 20% and 40%.
Note that these figures are on the full dataset, where the fraud rate is 0.13%. The fair comparison with the model uses steps ≥ 600 and is in the README.

## Sheet 2: `Results`
The control-effectiveness output from `05_controls.sql`.

## Sheet 3: `Exceptions`
The exception summary from `04_data_assurance_checks.sql`, plus a **PivotTable** of exceptions by `check_name` showing the average fraud share (%) per check.

## Sheet 4: `Sample_Review`
A stratified sample of 25 flagged transactions, 5 randomly selected per control, taken from `control_hits` joined to `gold_transactions` in Databricks (`ROW_NUMBER() OVER (PARTITION BY control_name ORDER BY rand())`, keeping `rn <= 5`). Each row has a `Reviewer conclusion` and `Comment` added by manual review. Result: 7 of 25 were actual fraud (C3 4/5, C4 3/5). Because rand() is unseeded, a rerun gives a different sample, so the exact rows drawn are saved in excel/sample_review_25.csv. The reviewer conclusions and comments are in the workbook's Sample_Review sheet.

## Sheet 5: `Thresholds`
The C1 threshold experiment (100K, 200K, 500K, 1M), with a line chart of precision vs recall by threshold.