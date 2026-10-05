-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 04 · Data assurance checks (Databricks SQL)
-- MAGIC Completeness, validity, accuracy and uniqueness checks run against `gold_transactions`.
-- MAGIC Every failure is logged to `dq_exceptions` rather than removed, so nothing is deleted
-- MAGIC from the underlying data.

-- COMMAND ----------

USE CATALOG workspace;
USE SCHEMA default;

-- COMMAND ----------

-- Six checks, unioned into one exceptions table so each failure can be traced back to a
-- single txn_id and a named check.
CREATE OR REPLACE TABLE dq_exceptions AS

-- DQ1 Completeness: missing key fields
SELECT txn_id, 'DQ1_missing_key_field' AS check_name,
       'NULL in type/amount/orig_account/dest_account' AS detail
FROM gold_transactions
WHERE type IS NULL OR amount IS NULL OR orig_account IS NULL OR dest_account IS NULL

UNION ALL
-- DQ2 Validity: zero or negative amount
SELECT txn_id, 'DQ2_non_positive_amount', CONCAT('amount=', amount)
FROM gold_transactions
WHERE amount <= 0

UNION ALL
-- DQ3 Accuracy: sender balance does not reconcile
SELECT txn_id, 'DQ3_orig_balance_mismatch',
       CONCAT(type, ' diff=', ROUND(orig_balance_error, 2))
FROM gold_transactions
WHERE ABS(orig_balance_error) > 0.01

UNION ALL
-- DQ4 Accuracy: receiver balance does not reconcile (customer accounts only —
--               merchant accounts carry no balance information in PaySim)
SELECT txn_id, 'DQ4_dest_balance_mismatch',
       CONCAT(type, ' diff=', ROUND(dest_balance_error, 2))
FROM gold_transactions
WHERE NOT dest_is_merchant
  AND type IN ('TRANSFER', 'CASH_OUT')
  AND ABS(dest_balance_error) > 0.01

UNION ALL
-- DQ5 Validity: payment larger than the sender's available balance
SELECT txn_id, 'DQ5_amount_exceeds_balance',
       CONCAT('amount=', amount, ' balance=', oldbalance_orig)
FROM gold_transactions
WHERE type IN ('TRANSFER', 'CASH_OUT', 'PAYMENT', 'DEBIT')
  AND amount > oldbalance_orig

UNION ALL
-- DQ6 Uniqueness: possible duplicate postings (same step, parties and amount)
SELECT g.txn_id, 'DQ6_possible_duplicate', CONCAT('group size=', d.n)
FROM gold_transactions g
JOIN (SELECT step, orig_account, dest_account, amount, COUNT(*) AS n
      FROM gold_transactions
      GROUP BY step, orig_account, dest_account, amount
      HAVING COUNT(*) > 1) d
  ON  g.step = d.step AND g.orig_account = d.orig_account
  AND g.dest_account = d.dest_account AND g.amount = d.amount;

-- COMMAND ----------

-- MAGIC %md ## Exception summary (Power BI page 1)

-- COMMAND ----------

-- For each check: how many rows failed it, what share of all transactions that is,
-- and how much of that is actual fraud — this is what separates a real risk signal
-- (DQ4) from a data-generation artifact (DQ3/DQ5).
SELECT e.check_name,
       COUNT(*)                                                                  AS exceptions,
       ROUND(100 * COUNT(*) / (SELECT COUNT(*) FROM gold_transactions), 3)       AS pct_of_txns,
       SUM(g.is_fraud)                                                           AS of_which_fraud,
       ROUND(100 * SUM(g.is_fraud) / COUNT(*), 2)                                AS fraud_share_pct
FROM dq_exceptions e
JOIN gold_transactions g USING (txn_id)
GROUP BY e.check_name
ORDER BY exceptions DESC;

-- COMMAND ----------

-- MAGIC %md
-- MAGIC ## Findings
-- MAGIC The three questions this analysis answers, and where the answers live:
-- MAGIC 1. Which check fails most often, and is it a data-quality problem or a risk signal?
-- MAGIC 2. Is the fraud share among exceptions much higher than the overall fraud rate?
-- MAGIC 3. What would be worth fixing at source?
-- MAGIC
-- MAGIC (Answered in full in the project README / findings notes.)