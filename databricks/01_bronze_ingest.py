# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Bronze: ingest raw PaySim data
# MAGIC The raw CSV is landed as a Delta table exactly as received, with lineage columns added,
# MAGIC and reconciled on row count / total amount / fraud count against the source file.
# MAGIC
# MAGIC A volume (e.g. `workspace.default.raw`) was created in Catalog Explorer and the PaySim
# MAGIC CSV uploaded into it ahead of running this, with the widgets below pointing at it.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "default")
dbutils.widgets.text("csv_path", "/Volumes/workspace/default/raw/PS_20174392719_1491204439457_log.csv")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
CSV_PATH = dbutils.widgets.get("csv_path")
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

# COMMAND ----------

from pyspark.sql import functions as F, types as T

# Schema is explicit rather than inferred, since financial data shouldn't have its types guessed
schema = T.StructType([
    T.StructField("step", T.IntegerType()),
    T.StructField("type", T.StringType()),
    T.StructField("amount", T.DecimalType(14, 2)),
    T.StructField("nameOrig", T.StringType()),
    T.StructField("oldbalanceOrg", T.DecimalType(14, 2)),
    T.StructField("newbalanceOrig", T.DecimalType(14, 2)),
    T.StructField("nameDest", T.StringType()),
    T.StructField("oldbalanceDest", T.DecimalType(14, 2)),
    T.StructField("newbalanceDest", T.DecimalType(14, 2)),
    T.StructField("isFraud", T.IntegerType()),
    T.StructField("isFlaggedFraud", T.IntegerType()),
])

raw = spark.read.csv(CSV_PATH, header=True, schema=schema)

bronze = (raw
          .withColumn("txn_id", F.monotonically_increasing_id())   # surrogate key, fixed once written
          .withColumn("_source_file", F.lit(CSV_PATH))
          .withColumn("_ingested_at", F.current_timestamp()))

bronze.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable("bronze_transactions")

# COMMAND ----------

# MAGIC %md ## Load reconciliation
# MAGIC These numbers were compared against the same figures computed from the CSV directly
# MAGIC (in pandas, locally), and both are recorded in the README. A mismatch would mean rows
# MAGIC were dropped or mis-parsed during load.

# COMMAND ----------

display(spark.sql("""
    SELECT COUNT(*)                                  AS rows_loaded,
           SUM(amount)                               AS total_amount,
           SUM(isFraud)                              AS fraud_rows,
           SUM(CASE WHEN type IS NULL OR amount IS NULL THEN 1 ELSE 0 END) AS unparsed_rows,
           MIN(step) AS first_step, MAX(step) AS last_step
    FROM bronze_transactions
"""))

display(spark.sql("""
    SELECT type, COUNT(*) AS txns, SUM(isFraud) AS frauds,
           ROUND(100 * SUM(isFraud) / COUNT(*), 4) AS fraud_rate_pct
    FROM bronze_transactions
    GROUP BY type ORDER BY frauds DESC
"""))