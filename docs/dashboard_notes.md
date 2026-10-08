# Power BI Dashboard Notes

## Power BI Page 1: Data Assurance
- Checks ran on all 6,362,620 transactions (the dashboard also shows the 2,770,409
  TRANSFER/CASH_OUT subset as a separate card) | Total exceptions flagged: ~7.47M (exceeds
  the row count because one transaction can fail multiple checks - UNION ALL)
- DQ3 (3.60M exceptions) and DQ5 (3.60M exceptions): ~0% fraud share -> confirms these are
  PaySim data-generation artifacts, not real fraud signals (matches the earlier finding)
- DQ4 (0.27M exceptions): 1.57% fraud share vs 0.13% overall baseline -> ~12x baseline,
  a genuine fraud risk signal despite far fewer exceptions than DQ3/DQ5
- DQ2 (near-zero exceptions): 100% fraud share, but sample too small to be meaningful
- Takeaway: exception volume and fraud relevance are not the same thing - DQ4 matters
  far more than its small count suggests

## Power BI Page 2: Control Effectiveness

Control effectiveness (5 controls):
| Control | Flagged | Frauds Caught | Precision % | Recall % |
|---|---|---|---|---|
| C2_account_drained | 1,188,074 | 8,012 | 0.67 | 97.55 |
| C4_transfer_then_cashout | 6,306 | 4,078 | 64.67 | 49.65 |
| C3_dest_no_balance_movement | 5,776 | 4,070 | 70.46 | 49.56 |
| C1_high_value_transfer | 409,110 | 2,740 | 0.67 | 33.36 |
| C5_orig_balance_mismatch | 2,488,652 | 45 | 0.00 | 0.55 |

Frauds missed by all 5 controls combined: 17 (out of 8,213 total)

Interpretation:
- C3 and C4 are the most balanced controls - both catch roughly half of all fraud
  (~50% recall) while staying reasonably precise (65-70%).
- C2 has near-total recall (97.55%) but almost no precision (0.67%) - it catches
  almost every fraud but also flags 1.19 million non-fraud transactions, which would
  overwhelm an investigations team in practice.
- C5 is close to useless: flags 2.49 million transactions (the most of any control)
  but catches only 45 frauds - high volume, almost no value. A candidate to drop or
  redesign.
- Combined, all 5 controls only miss 17 of 8,213 total frauds - strong overall
  coverage, but achieved mostly by C2's very high false-positive rate.

C1 threshold trade-off (high-value transfer rule):
| Threshold | Flagged | Frauds Caught | Precision % | Recall % |
|---|---|---|---|---|
| 100,000 | 470,866 | 3,255 | 0.69 | 39.63 |
| 200,000 | 409,110 | 2,740 | 0.67 | 33.36 |
| 500,000 | 261,068 | 1,940 | 0.74 | 23.62 |
| 1,000,000 | 128,859 | 1,361 | 1.06 | 16.57 |

Interpretation:
Raising the amount threshold sharply reduces recall (39.63% -> 16.57%) for only a
small precision gain (0.69% -> 1.06%). This shows C1 alone is a weak control: no
threshold makes it both high-precision and high-recall, which is why combining it
with the other controls (not relying on amount alone) matters more than fine-tuning
this one rule.

## Power BI Page 3: Fraud Patterns

Fraud count & value by type:
- CASH_OUT: ~4.1K frauds, ~5,989M amount
- TRANSFER: ~4.1K frauds, ~6,067M amount
Interpretation: Fraud count and value are split almost evenly between TRANSFER and
CASH_OUT. This matches the earlier finding that a fraudulent TRANSFER is almost always
immediately followed by a matching fraudulent CASH_OUT of the same amount (the mule
pattern, confirmed by matched_fraud_pairs = 4,308) - so each fraud event shows up
twice in the data, once per type.

Fraud count by hour of day:
Hour: 0=300, 3=372, 4=274, 5=366, 10=375, 15=341, 20=340, 22=351, 23=323
(full range roughly 274-375 across all 24 hours)
Interpretation: Fraud count is roughly uniform across all 24 hours, with no hour
standing out. This contrasts with legitimate transaction volume (from the forecast
work), which has a strong repeating hour-of-day pattern. This means "time of
day" is not a useful standalone signal for flagging fraud in this dataset - unlike
transaction volume, fraud doesn't cluster around specific hours.

Daily trend (txns and frauds by day_number):
- Days 1-17: transaction volume high and stable (~0.35M-0.58M/day)
- Days 18-31: transaction volume drops sharply (~0.01M-0.06M/day)
- Fraud count stays roughly steady throughout (~210-320 frauds/day), regardless of
  the volume drop

Interpretation:
Transaction volume collapses after day 17 (likely a PaySim simulation artifact -
less overall activity generated in later steps), but fraud volume does not drop
with it, so the fraud rate is much higher in the back half of the dataset. This is
relevant to the model: the time-based train/test split (step 600, around day
25) falls inside this low-volume period, meaning the test set is not representative
of "normal" days - a limitation worth noting for the model's real-world reliability.

## Power BI Page 4: Model & Forecast

Confusion matrix (Random Forest, test period):
TN=41,950 | FP=0 | FN=1 | TP=1,617

Model metrics:
- Logistic Regression: PR-AUC 0.9588, Precision 52.16%, Recall 97.16%
- Random Forest: PR-AUC 1.0000, Precision 100.00%, Recall 99.94% (inflated by leakage,
  as noted in the model notes)

Rules vs model comparison (same test window, step >= 600, for a fair comparison):
- Random Forest: 99.94% recall, 100.00% precision (inflated by leakage, not a genuine
  comparison point)
- Logistic Regression: 97.16% recall, 52.16% precision
- C3 (dest no balance movement): 50.00% recall, 100.00% precision
- C4 (transfer-then-cashout): 49.63% recall, 98.65% precision
Interpretation: Once the random forest's inflated numbers are set aside, C3 and C4
actually match or beat logistic regression on precision (98-100% vs 52.16%), at
roughly half the recall. The earlier framing (ML beats every rule) only holds against
the weak controls (C1, C2, C5) - not against C3/C4, this project's two defensible
controls, once measured on the same population.

Forecast back-test (steps 720-743):
Forecast target is fraud count per hour, not transaction volume. Actual fraud stays
in the 4-28 range throughout this window, with no strong pattern. Seasonal naive
(MAE 5.92) and regression (MAE 4.38) both track this reasonably well; regression is
chosen since it beats the baseline. Unlike transaction volume, fraud count doesn't
collapse in the low-volume tail (days 18-31, see Page 3), so this back-test window is
actually representative of fraud behavior generally, even though it falls in an
atypical period for transaction volume. (An earlier version of this back-test was run
against transaction volume and mislabeled as a fraud forecast - the MAE 463/1,249
figures from that version are no longer current.)

## Tableau Public: Fraud Heatmap (day_number × hour_of_day)
- A heatmap (Square marks, Color = SUM(Frauds)) was built with day_number on Columns
  and hour_of_day on Rows
- Coloring is roughly uniform across all day/hour cells — light-to-medium shade
  throughout, with only a few scattered darker squares and no consistent dark
  block, stripe, or diagonal
- Confirms the Page 3 finding (fraud by hour of day is roughly flat, ~274-375 per
  hour): fraud does not cluster by time of day or by day of the dataset
- Takeaway: a control that increases monitoring during specific hours would not
  be supported by this data — fraud risk is evenly distributed across time,
  not concentrated in a window

## Tableau Public: Transactions vs Frauds Over Time (dual-axis line)
- A dual-axis line chart shows Txns (left axis, 0-50K) vs Frauds (right axis, 0-40) by Step
- Txns swings sharply between near-zero and ~50K in the first ~400 steps (~17 days),
  then collapses into a low, flat band for the rest of the series
- Frauds keeps oscillating in roughly the same 0-40 range throughout, showing no
  corresponding drop after the volume collapse
- Reinforces the Page 3 daily-trend finding: fraud volume is largely independent of
  overall transaction volume, which matters for the model's test-split and
  forecast back-test (both evaluated mostly on the sparse tail period)

## Tableau Public: Published
- Published dashboard: https://public.tableau.com/app/profile/aditya.ranjan7019/viz/PaymentFraudRiskAnalytics-PaySim/FraudAnalyticsDashboard
- Combines both visuals (Fraud Heatmap, Transaction Volume vs Fraud Count) on one dashboard

## Excel Workpaper: Sample_Review
- Stratified sample: 5 randomly selected flagged transactions per control (25 total), joined from control_hits + gold_transactions in Databricks and reviewed manually against is_fraud
- Result: 7/25 were actual fraud. C3 4/5, C4 3/5, C1 0/5, C2 0/5, C5 0/5
- C3 and C4 hits that were fraud show the same pattern: a full-balance TRANSFER into a destination with no balance movement
- C1 and C2 hits were legitimate large transfers or cash-outs that drained an account. C5 hits were the known PaySim balance artifact (oldbalance_orig = 0 or fields inconsistent with the amount)
- Two C4 hits were false positives: 10,000,000 transfers matched to unrelated same-amount cash-outs. C4 has no account link, and 10,000,000 is PaySim's transfer cap
- Consistent with the full-dataset results: C3 and C4 are the useful controls, C1, C2 and C5 produce mostly false positives. With 5 rows per control this is an illustration, not a statistical estimate

## Excel Workpaper: Thresholds
- A line chart plots precision_pct vs recall_pct across C1 thresholds (100K, 200K, 500K, 1M)
- Recall drops steadily from 39.63% to 16.57% as threshold increases
- Precision stays extremely low throughout (0.67% to 1.06%) — raising the threshold barely
  improves precision because high-value transfers are rarely fraud regardless of amount
- Matches the same trade-off shown in Power BI Page 2


## Excel Workpaper: Summary
- The Summary sheet uses XLOOKUP formulas pulling Flagged and Frauds caught from the Results sheet
- Precision % = Frauds caught / Flagged; Recall % = Frauds caught / Total actual frauds (8,213) — both live formulas
- Conditional formatting on Recall %: green ≥40% (Effective), red <20% (Ineffective), unformatted 20-40% (Partial)
- Conclusions: C3 and C4 effective (balanced precision/recall), C1 and C2 partially effective (high
  recall but very low precision), C5 ineffective (near-zero recall despite largest flagged volume)
- Final take: only 2 of 5 controls (C3, C4) would be worth keeping as-is; C5 should likely be
  retired or redesigned since it's mostly a data artifact, not a fraud signal