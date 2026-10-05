-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 05 · Rule-based controls + control effectiveness testing
-- MAGIC Five detective controls were built and each tested for precision (how much of what
-- MAGIC it flags is real fraud) and recall (how much of all fraud it actually catches).

-- COMMAND ----------

USE CATALOG workspace;
USE SCHEMA default;

-- COMMAND ----------

-- The five controls, unioned into one hits table keyed by txn_id and control_name so
-- effectiveness can be measured per control and combined.
CREATE OR REPLACE TABLE control_hits AS

-- C1 High-value transfer (mirrors the simulator's own 200,000 rule)
SELECT txn_id, 'C1_high_value_transfer' AS control_name
FROM gold_transactions
WHERE type = 'TRANSFER' AND amount >= 200000

UNION
-- C2 Account drained in one transaction
SELECT txn_id, 'C2_account_drained'
FROM gold_transactions
WHERE type IN ('TRANSFER', 'CASH_OUT')
  AND oldbalance_orig > 0 AND newbalance_orig = 0 AND amount >= oldbalance_orig

UNION
-- C3 Receiving customer account shows no balance movement despite money arriving
SELECT txn_id, 'C3_dest_no_balance_movement'
FROM gold_transactions
WHERE type IN ('TRANSFER', 'CASH_OUT')
  AND NOT dest_is_merchant AND amount > 0 AND dest_zero_both = 1

UNION
-- C4 Transfer followed by a cash-out of the same amount within 1 step.
--    There is no account link: matching on orig_account = dest_account returned 0 matches
--    in PaySim (see docs/controls_alteryx_notes.md), so same-amount timing is used instead.
--    Some matches are coincidental, since PaySim caps transfers at 10,000,000.
SELECT t1.txn_id, 'C4_transfer_then_cashout'
FROM gold_transactions t1
JOIN gold_transactions t2
  ON  t2.type = 'CASH_OUT'
  AND t2.step BETWEEN t1.step AND t1.step + 1
  AND t2.amount = t1.amount
WHERE t1.type = 'TRANSFER'

UNION
-- C5 Sender balance does not reconcile on money-out transactions (reuses DQ3)
SELECT e.txn_id, 'C5_orig_balance_mismatch'
FROM dq_exceptions e
JOIN gold_transactions g USING (txn_id)
WHERE e.check_name = 'DQ3_orig_balance_mismatch'
  AND g.type IN ('TRANSFER', 'CASH_OUT');

-- COMMAND ----------

-- MAGIC %md ## Control effectiveness (Power BI page 2)

-- COMMAND ----------

-- Precision and recall per control, which is what separates the two genuinely useful
-- controls (C3, C4) from the ones that flag heavily but catch little (C1, C2, C5).
SELECT c.control_name,
       COUNT(*)                                                               AS flagged,
       SUM(g.is_fraud)                                                        AS frauds_caught,
       ROUND(100 * SUM(g.is_fraud) / COUNT(*), 2)                             AS precision_pct,
       ROUND(100 * SUM(g.is_fraud) / (SELECT SUM(is_fraud) FROM gold_transactions), 2) AS recall_pct
FROM control_hits c
JOIN gold_transactions g USING (txn_id)
GROUP BY c.control_name
ORDER BY recall_pct DESC;

-- COMMAND ----------

-- All five controls combined
SELECT COUNT(DISTINCT c.txn_id)                                     AS flagged_by_any,
       COUNT(DISTINCT CASE WHEN g.is_fraud = 1 THEN c.txn_id END)   AS frauds_caught_by_any,
       (SELECT SUM(is_fraud) FROM gold_transactions)                AS total_frauds
FROM control_hits c
JOIN gold_transactions g USING (txn_id);

-- COMMAND ----------

-- Frauds that no control caught — this is the gap the ML model (06_fraud_model.py)
-- was built to close.
CREATE OR REPLACE TABLE frauds_missed_by_rules AS
SELECT g.*
FROM gold_transactions g
LEFT ANTI JOIN control_hits c USING (txn_id)
WHERE g.is_fraud = 1;

SELECT type, COUNT(*) AS missed_frauds, SUM(amount) AS missed_amount
FROM frauds_missed_by_rules
GROUP BY type;

-- COMMAND ----------

-- MAGIC %md ## Threshold experiment for C1 (precision vs recall trade-off)

-- COMMAND ----------

-- Re-runs C1 at several amount thresholds to show how precision and recall trade off
-- as the cutoff moves — the basis for the Thresholds sheet/chart in the workpaper.
SELECT threshold,
       SUM(CASE WHEN amount >= threshold THEN 1 ELSE 0 END)                AS flagged,
       SUM(CASE WHEN amount >= threshold THEN is_fraud ELSE 0 END)         AS frauds_caught,
       ROUND(100 * SUM(CASE WHEN amount >= threshold THEN is_fraud ELSE 0 END)
             / NULLIF(SUM(CASE WHEN amount >= threshold THEN 1 ELSE 0 END), 0), 2) AS precision_pct,
       ROUND(100 * SUM(CASE WHEN amount >= threshold THEN is_fraud ELSE 0 END)
             / (SELECT SUM(is_fraud) FROM gold_transactions), 2)           AS recall_pct
FROM gold_transactions
CROSS JOIN (VALUES (100000), (200000), (500000), (1000000)) AS th(threshold)
WHERE type = 'TRANSFER'
GROUP BY threshold
ORDER BY threshold;

-- COMMAND ----------

-- The simulator's own built-in control, included here as a benchmark for comparison
SELECT SUM(is_flagged_fraud)            AS flagged_by_system,
       SUM(is_flagged_fraud * is_fraud) AS true_frauds_flagged_by_system,
       SUM(is_fraud)                    AS total_frauds
FROM gold_transactions;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Exports feeding the other tools
-- MAGIC These query results were downloaded as CSV and used downstream in Alteryx, Python,
-- MAGIC Power BI, Tableau and Excel:
-- MAGIC 1. `SELECT * FROM gold_transactions WHERE type IN ('TRANSFER','CASH_OUT')` → `gold_transfer_cashout.csv`
-- MAGIC 2. `SELECT * FROM gold_hourly_summary` → `gold_hourly_summary.csv`
-- MAGIC 3. The control-effectiveness and exception-summary results → small CSVs for Power BI / Excel
-- MAGIC
-- MAGIC Where a download was too large for the UI, a filtered or sampled version was exported
-- MAGIC instead, noted as such in the README.