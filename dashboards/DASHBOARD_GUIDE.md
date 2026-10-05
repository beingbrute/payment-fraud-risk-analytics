# Dashboard Guide

## Power BI Desktop (Windows): `payment_controls.pbix`
The `.pbix` file is about 320 MB, over GitHub's 100 MB limit, so it is not in this repo.
Screenshots of all four pages are in the README (Section 6).

Data: CSV exports from Databricks (exception summary, control effectiveness, threshold
experiment, gold_hourly_summary) plus `model_scores_test.csv`, `forecast_next_24h.csv`,
and `forecast_backtest.csv` from the Python scripts. The "rules vs model" comparison on
page 4 is a small table entered by hand in Power Query, using the controls re-run on the
model's test window (step ≥ 600).

| Page | Visuals |
|---|---|
| 1 · Data Assurance | KPI cards (rows loaded, exceptions, % of transactions). Bar: exceptions by check. Column: fraud share per check vs overall fraud rate |
| 2 · Control Effectiveness | Clustered bar: flagged vs frauds caught per control. Precision & recall by control. Card: frauds missed by all controls. Line: C1 threshold trade-off |
| 3 · Fraud Patterns | Fraud count & value by type. Fraud by hour of day. Daily trend from gold_hourly_summary |
| 4 · Model & Forecast | Confusion matrix (matrix visual). Precision / recall / PR-AUC cards for both models. Rules vs model comparison. Line: back-test actual vs forecast + next-24h forecast |

Precision and recall are DAX measures (e.g. `Precision % = DIVIDE([Frauds Caught],[Flagged])`).

## Tableau Public: 1 published dashboard
- Workbook: `tableau/payment_fraud_analytics.twbx` (packaged workbook, data included)
- Data: `gold_hourly_summary.csv` (small, no account IDs)
- Views: a heatmap of fraud count by **day_number × hour_of_day** (both computed from
  `step` as calculated fields: hour = `step % 24`, day = `FLOOR((step−1)/24)+1`), and a
  dual-axis line of transactions vs frauds over time. The hour convention is the same
  as in the Gold table, Python and Power BI.
- Published dashboard: https://public.tableau.com/app/profile/aditya.ranjan7019/viz/PaymentFraudRiskAnalytics-PaySim/FraudAnalyticsDashboard

Anything published to Tableau Public is visible to anyone on the internet.