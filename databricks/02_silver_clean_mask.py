# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver: clean, standardise and mask
# MAGIC Column names and types are standardised, a merchant flag is added, and account IDs are
# MAGIC hashed so no raw identifiers leave this layer — part of handling the data responsibly.
# MAGIC
# MAGIC No rows are deleted here. Data-quality problems are logged later (04 SQL), not removed.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "default")
dbutils.widgets.text("hash_salt", "change-me-and-do-not-commit")   # the real value is kept out of GitHub

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
SALT = dbutils.widgets.get("hash_salt")
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------

from pyspark.sql import functions as F

b = spark.table("bronze_transactions")

def masked(col):
    # Salted SHA-256: the same account always gets the same hash, so joins still work,
    # but the original ID can't be read back from it.
    return F.sha2(F.concat(F.lit(SALT), F.col(col)), 256)

silver = (b.select(
            "txn_id",
            "step",
            F.upper(F.trim("type")).alias("type"),
            "amount",
            masked("nameOrig").alias("orig_account"),
            F.col("oldbalanceOrg").alias("oldbalance_orig"),
            F.col("newbalanceOrig").alias("newbalance_orig"),
            masked("nameDest").alias("dest_account"),
            # The merchant flag is derived before hashing, since merchant IDs start with 'M'
            F.col("nameDest").startswith("M").alias("dest_is_merchant"),
            F.col("oldbalanceDest").alias("oldbalance_dest"),
            F.col("newbalanceDest").alias("newbalance_dest"),
            F.col("isFraud").alias("is_fraud"),
            F.col("isFlaggedFraud").alias("is_flagged_fraud"),
            "_ingested_at"))

silver.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("silver_transactions")

# COMMAND ----------

# MAGIC %md ## Checks: row count unchanged, no raw IDs left

# COMMAND ----------

display(spark.sql("""
    SELECT (SELECT COUNT(*) FROM bronze_transactions) AS bronze_rows,
           (SELECT COUNT(*) FROM silver_transactions) AS silver_rows,
           (SELECT SUM(amount) FROM bronze_transactions) AS bronze_amount,
           (SELECT SUM(amount) FROM silver_transactions) AS silver_amount
"""))

# This returns 0, confirming no column in silver still carries a raw C.../M... account ID
display(spark.sql("""
    SELECT COUNT(*) AS rows_with_raw_ids
    FROM silver_transactions
    WHERE orig_account RLIKE '^[CM][0-9]+$' OR dest_account RLIKE '^[CM][0-9]+$'
"""))