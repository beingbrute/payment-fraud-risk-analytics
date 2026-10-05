-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 03 · Gold: analysis-ready tables
-- MAGIC - `gold_transactions`: silver plus derived fields used by the controls, the ML models
-- MAGIC   and the dashboards
-- MAGIC - `gold_hourly_summary`: one row per step (hour), used for trend charts and the forecast

-- COMMAND ----------

USE CATALOG workspace;
USE SCHEMA default;

-- COMMAND ----------

-- orig_balance_error / dest_balance_error flag where the balance math doesn't reconcile
-- (used later as data-quality checks and as model features); orig_drained and
-- dest_zero_both are simple flags picked up by a couple of the fraud controls.
CREATE OR REPLACE TABLE gold_transactions AS
SELECT
    s.*,
    step % 24                                   AS hour_of_day,
    CAST(FLOOR((step - 1) / 24) + 1 AS INT)     AS day_number,
    CASE WHEN type = 'CASH_IN'
         THEN oldbalance_orig + amount - newbalance_orig
         ELSE oldbalance_orig - amount - newbalance_orig END   AS orig_balance_error,
    oldbalance_dest + amount - newbalance_dest                 AS dest_balance_error,
    CASE WHEN oldbalance_orig > 0 AND newbalance_orig = 0 THEN 1 ELSE 0 END AS orig_drained,
    CASE WHEN oldbalance_dest = 0 AND newbalance_dest = 0 THEN 1 ELSE 0 END AS dest_zero_both
FROM silver_transactions s;

-- COMMAND ----------

-- One row per hour (step), rolled up for the volume/fraud trend charts and as the input
-- series for the forecasting script.
CREATE OR REPLACE TABLE gold_hourly_summary AS
SELECT step,
       COUNT(*)                                        AS txns,
       SUM(amount)                                     AS total_amount,
       SUM(is_fraud)                                   AS frauds,
       SUM(CASE WHEN is_fraud = 1 THEN amount ELSE 0 END) AS fraud_amount
FROM gold_transactions
GROUP BY step
ORDER BY step;

-- COMMAND ----------

-- Reconciliation check: row count and total amount should match silver_transactions
SELECT COUNT(*) AS gold_rows, SUM(amount) AS gold_amount FROM gold_transactions;