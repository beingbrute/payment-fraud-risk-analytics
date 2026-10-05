import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data_exports/forecast_backtest.csv")

sn_mae = (df["actual"] - df["seasonal_naive"]).abs().mean()
reg_mae = (df["actual"] - df["regression"]).abs().mean()

plt.figure(figsize=(12, 6))
plt.plot(df["step"], df["actual"], color="black", marker="o", label="Actual frauds", linewidth=2)
plt.plot(df["step"], df["seasonal_naive"], color="#3b82f6", marker="o", label=f"Seasonal naive (MAE {sn_mae:.2f})")
plt.plot(df["step"], df["regression"], color="#ef4444", marker="o", label=f"Regression (MAE {reg_mae:.2f})")

plt.title("24-Hour Back-Test: Actual vs Forecast Fraud Count", fontsize=14, fontweight="bold")
plt.xlabel("Step (hour)")
plt.ylabel("Fraud count")
plt.legend(loc="upper left")
plt.grid(axis="y", linestyle="--", alpha=0.5)
plt.tight_layout()

plt.savefig("docs/screenshots/forecast.png", dpi=150)
print("Saved to docs/screenshots/forecast.png")