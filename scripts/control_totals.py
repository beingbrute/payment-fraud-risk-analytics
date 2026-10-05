import pandas as pd

df = pd.read_csv("PS_20174392719_1491204439457_log.csv")

print("row count:", len(df))
print("total amount:", df["amount"].sum())
print("fraud count:", df["isFraud"].sum())
print("flagged fraud count:", df["isFlaggedFraud"].sum())
print("step range:", df["step"].min(), "-", df["step"].max())