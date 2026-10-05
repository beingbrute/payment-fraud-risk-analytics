import pandas as pd

df1 = pd.read_csv("gold_transfer_cashout.csv")
print("transfer_cashout rows:", len(df1))
print("types present:", df1["type"].unique())

df2 = pd.read_csv("gold_hourly_summary.csv")
print("hourly_summary rows:", len(df2))